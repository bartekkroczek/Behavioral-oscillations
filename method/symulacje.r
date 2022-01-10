setwd("~/projekty/r/behosc/")

library(signal)
library(ggplot2)

# Średnia krocząca ale daje wynik o długości równej długości danych.
# kosztem jest zwiększnie wag końców danych.
e2erollmean <- function(x, k) {
  ret <- NULL
  for (i in seq(length(x))) {
    ret[i] <- mean(x[seq(
      max(1, ceiling(i - (k - 1) / 2)),
      min(length(x), ceiling(i + (k - 1) / 2))
    )])
  }
  ret
}

repo_low <- "https://raw.githubusercontent.com/bartekkroczek/Behavioral-oscillations/master/data/low_resolution/"
files_low <- read.table("files_low.txt")$V1
freq_low <- 1 / 60
repo_high <- "https://raw.githubusercontent.com/bartekkroczek/Behavioral-oscillations/master/data/high_resolution/"
files_high <- read.table("files_high.txt")$V1
freq_high <- 1 / 120

d1 <- NULL
for (i in files_low) d1 <- rbind(d1, read.csv(paste0(repo_low, i)))
d1$Corr <- as.numeric(as.factor(d1$Corr)) - 1
d2 <- NULL
for (i in files_high) d2 <- rbind(d2, read.csv(paste0(repo_high, i)))
d2$PART_ID[d2$PART_ID == "160M25S2"] <- "160K25S2"
d2$Corr <- as.numeric(as.factor(d2$Corr)) - 1

d1$id <- d1$PART_ID
d1 <- subset(d1, Trial_type == "experiment")
d1atemp <- aggregate(Corr ~ PART_ID, d1, FUN = mean)
d1a <- aggregate(Corr ~ CSI * PART_ID * id, d1, FUN = mean)
d1a <- subset(d1a, PART_ID %in% d1atemp$PART_ID[d1atemp$Corr > .6])
d1a$t <- with(d1a, CSI * freq_low * 1000)
d1a$relt <- d1a$t - min(d1a$t)

d2$id <- substr(d2$PART_ID, 1, 6)
d2 <- subset(d2, Trial_type == "experiment")
d2atemp <- aggregate(Corr ~ PART_ID, d2, FUN = mean)
d2a <- aggregate(Corr ~ CSI * PART_ID * id, d2, FUN = mean)
d2a <- subset(d2a, PART_ID %in% d2atemp$PART_ID[d2atemp$Corr > .6])
d2a$t <- with(d2a, CSI * freq_high * 1000)
d2a$relt <- d2a$t - min(d2a$t)

## Dane losowe
wygeneruj_dane <- function(nid, nobspid, par1 = 5.728981, par2 = 1.471350, dist = rbeta) {
  data.frame(
    Corr = dist(nid * nobspid, par1, par2),
    relt = rep(seq(0, 1, length = nobspid), nid),
    PART_ID = rep(as.character(seq(nid)), each = nobspid),
    id = rep(as.character(seq(nid)), each = nobspid)
  )
}

nrand_id <- 33
randfreq <- 60
d3a <- wygeneruj_dane(nrand_id, randfreq)

permutuj_dane <- function(orgdat, notreally = FALSE) {
  ret <- orgdat
  if (!notreally) {
    for (i in unique(ret$PART_ID)) ret$relt[ret$PART_ID == i] <- sample(ret$relt[ret$PART_ID == i])
  }
  ret
}

d4a <- permutuj_dane(d1a)
d5a <- wygeneruj_dane(nrand_id, randfreq, .5, 1, runif)

trendtyp <- "rollm"
usun_trend <- function(dane, krok, typ = "rollm") {
  ret <- dane
  ret$trend <- NA
  if (typ == "rollm") {
    for (i in unique(ret$PART_ID)) {
      ret$trend[ret$PART_ID == i] <- e2erollmean(ret$Corr[ret$PART_ID == i], round(krok))
    }
  } else if (typ == "lm") {
    m <- lm(Corr ~ relt * PART_ID, ret)
    ret$trend <- predict(m)
  } else if (typ == "lpf") {
    for (i in unique(ret$PART_ID)) {
      ret$trend[ret$PART_ID == i] <- signal::filter(butter(2, .1, type = "low"), scale(ret$Corr[ret$PART_ID == i], sc = F)) + mean(ret$Corr[ret$PART_ID == i])
    }
  } else if (typ == "mean") {
    for (i in unique(ret$PART_ID)) {
      ret$trend[ret$PART_ID == i] <- mean(ret$Corr[ret$PART_ID == i])
    }
  } else if (typ == "none") {
    ret$trend <- 0
  } else {
    stop("Niewłaściwy argument 'typ'")
  }
  ret$Corr1 <- ret$Corr - ret$trend
  ret
}


d1a <- usun_trend(d1a, 200 / mean(diff(sort(unique(d1a$relt)))), typ = trendtyp) # krok ≈ 200 ms za Chen etal 2017
d2a <- usun_trend(d2a, 200 / mean(diff(sort(unique(d2a$relt)))), typ = trendtyp)
d3a <- usun_trend(d3a, randfreq / 5, typ = trendtyp)
d4a <- usun_trend(d4a, 200 / mean(diff(sort(unique(d4a$relt)))), typ = trendtyp)

hann <- function(dane) {
  ret <- dane
  ret$Corr2 <- NA
  for (i in unique(ret$PART_ID)) {
    ret$Corr2[ret$PART_ID == i] <- ret$Corr1[ret$PART_ID == i] * signal::hanning(length(ret$Corr1[ret$PART_ID == i]))
  }
  ret
}

d1a <- hann(d1a)
d2a <- hann(d2a)
d3a <- hann(d3a)
d4a <- hann(d4a)

fourier <- function(dane, zmienna = "Corr2") {
  ret <- NULL
  for (i in unique(dane$PART_ID)) {
    ret <- rbind(ret, data.frame(
      fft = Mod(with(subset(dane, PART_ID == i), fft(eval(as.name(zmienna))[order(relt)]))),
      Freq = with(subset(dane, PART_ID == i), seq(length(eval(as.name(zmienna)))) - 1),
      PART_ID = i,
      id = dane$id[dane$PART_ID == i][1]
    ))
  }
  ret
}

ffttab1 <- fourier(d1a)
ffttab2 <- fourier(d2a)
ffttab3 <- fourier(d3a)
ffttab4 <- fourier(d4a)

ffttab1$Hz <- ffttab1$Freq / max(d1a$relt) * 1000
ffttab2$Hz <- ffttab2$Freq / max(d2a$relt) * 1000
ffttab3$Hz <- ffttab3$Freq / max(d3a$relt)
ffttab4$Hz <- ffttab4$Freq / max(d4a$relt) * 1000

przypisz_pasma <- function(dane) {
  ret <- dane
  ret$band <- NA
  ret$band[ret$Hz >= 1 & ret$Hz < 4] <- "01delta"
  ret$band[ret$Hz >= 4 & ret$Hz < 8] <- "04theta"
  ret$band[ret$Hz >= 8 & ret$Hz < 12] <- "08alpha"
  ret$band[ret$Hz >= 12 & ret$Hz < 25] <- "12beta"
  ret
}

ffttab1 <- przypisz_pasma(ffttab1)
ffttab2 <- przypisz_pasma(ffttab2)
ffttab3 <- przypisz_pasma(ffttab3)
ffttab4 <- przypisz_pasma(ffttab4)

ffttab1$res <- "low"
ffttab2$res <- "high"
ffttab3$res <- "noise"
ffttab4$res <- "permuted"
ffttab <- rbind(ffttab1, ffttab2, ffttab3, ffttab4)

w1 <- ggplot(subset(ffttab, Hz < 31), aes(Hz, fft)) +
  stat_summary(aes(colour = res), geom = "line", fun = mean) +
  stat_summary(aes(fill = res), geom = "ribbon", fun.data = "mean_cl_boot", alpha = .1) +
  stat_summary(aes(colour = res, shape = band), geom = "point", fun = mean, size = 3)

## Liczba próbek dla dwóch kolejnych symulacji
ntem <- 10000
y <- rep(0, ntem)
for (i in 10000 / (seq(10, 190, by = 20) * pi * 2)) {
  y <- y + sin((1:ntem) / i)
}

## Wpływ średniej kroczączej
layout(matrix(1:9, nrow = 3, byrow = T))
plot(Mod(fft(y))[1:(2 * ntem / 100)] / ntem, t = "l", ylim = c(0, .6), xlab = "Bez filtra", ylab = "")
for (i in c(25, 50, 75, 100, 125, 150, 175, 200)) {
  plot(Mod(fft(y - e2erollmean(y, i)))[1:(2 * ntem / 100)] / ntem, t = "l", ylim = c(0, .6), xlab = paste("Krok =", i), ylab = "")
}

## to samo ale z filtrem dolnoprzepustowym
layout(matrix(1:9, nrow = 3, byrow = T))
plot(Mod(fft(y))[1:(2 * ntem / 100)] / ntem, t = "l", ylim = c(0, 1), xlab = "Bez filtra", ylab = "")
for (i in c(2, 3, 4, 5, 6, 7, 8, 9)) {
  plot(Mod(fft(y - signal::filter(butter(i, .1, type = "low"), y)))[1:(2 * ntem / 100)] / ntem, t = "l", ylim = c(0, 1), xlab = paste("Order =", i), ylab = "")
}

## ilustracja efektu
ggplot(data.frame(
  x = rep(seq(600), 5),
  y = c(
    sin((1:600) / 30),
    sin((1:600) / 10),
    sin((1:600) / 30) + sin((1:600) / 10),
    e2erollmean(sin((1:600) / 30) + sin((1:600) / 10), 100),
    sin((1:600) / 30) + sin((1:600) / 10) - e2erollmean(sin((1:600) / 30) + sin((1:600) / 10), 100)
  ),
  dane = rep(c("A_30", "B_10", "C_30+10", "D_roll", "E_10+30-roll"), each = 600)
), aes(x, y)) +
  geom_line() +
  facet_grid(dane ~ .)
