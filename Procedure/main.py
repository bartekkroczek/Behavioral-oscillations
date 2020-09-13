#!/usr/bin/env python
# -*- coding: latin-1 -*-
import atexit
import codecs
import csv
import random
from os.path import join

import yaml
from psychopy import visual, event, logging, gui, core

from misc.screen_misc import get_screen_res, get_frame_rate
from itertools import combinations_with_replacement, product

# GLOBALS


logging.LogFile(join('results', 'PART_ID' + '.log'), level=logging.INFO)  # errors logging
RESULTS = list()
RESULTS.append(['PART_ID', 'Trial_no', 'Trial_type', 'CSI', 'Stim_letter', 'Key_pressed', 'letter_choose', 'Rt', 'Corr'])


@atexit.register
def save_beh_results():
    with open(join('results', PART_ID + '_' + str(random.choice(range(100, 1000))) + '_beh.csv'), 'w') as beh_file:
        beh_writer = csv.writer(beh_file)
        beh_writer.writerows(RESULTS)
    logging.flush()


def read_text_from_file(file_name, insert=''):
    """
    Method that read message from text file, and optionally add some
    dynamically generated info.
    :param file_name: Name of file to read
    :param insert:
    :return: message
    """
    if not isinstance(file_name, str):
        logging.error('Problem with file reading, filename must be a string')
        raise TypeError('file_name must be a string')
    msg = list()
    with codecs.open(file_name, encoding='utf-8', mode='r') as data_file:
        for line in data_file:
            if not line.startswith('#'):  # if not commented line
                if line.startswith('<--insert-->'):
                    if insert:
                        msg.append(insert)
                else:
                    msg.append(line)
    return ''.join(msg)


def check_exit(key='f7'):
    stop = event.getKeys(keyList=[key])
    if stop:
        abort_with_error('Experiment finished by user! {} pressed.'.format(key))


def show_info(win, file_name, insert=''):
    """
    Clear way to show info message into screen.
    :param win:
    :return:
    """
    msg = read_text_from_file(file_name, insert=insert)
    msg = visual.TextStim(win, color='black', text=msg, height=20, wrapWidth=SCREEN_RES['width'])
    msg.draw()
    win.flip()
    key = event.waitKeys(keyList=['f7', 'return', 'space', 'left', 'right'])
    if key == ['f7']:
        abort_with_error('Experiment finished by user on info screen! F7 pressed.')
    win.flip()


def abort_with_error(err):
    logging.critical(err)
    raise Exception(err)


def determine_time_value(val):
    if isinstance(val, int):
        return val
    elif isinstance(val, str) and '-' in val:
        min, max = val.split('-')
        return random.choice(range(int(min), int(max)))


def main():
    global PART_ID  # PART_ID is used in case of error on @atexit, that's why it must be global
    # === Dialog popup ===
    info = {'IDENTYFIKATOR': '', u'P\u0141EC': ['M', "K"], 'WIEK': '20'}
    dictDlg = gui.DlgFromDict(dictionary=info, title='Czas detekcji wzrokowej')
    if not dictDlg.OK:
        abort_with_error('Info dialog terminated.')

    clock= core.Clock()
    conf = yaml.load(open('config.yaml'))
    # === Scene init ===
    win = visual.Window(list(SCREEN_RES.values()), fullscr=True, monitor='testMonitor', units='pix',
                                       screen=0, color=conf['BACKGROUND_COLOR'])
    event.Mouse(visible=False, newPos=None, win=win)  # Make mouse invisible
    FRAME_RATE = get_frame_rate(win)
    if FRAME_RATE != conf['FRAME_RATE']:
        dlg = gui.Dlg(title="Critical error")
        dlg.addText('Wrong no of frames detected: {}. Experiment terminated.'.format(FRAME_RATE))
        dlg.show()
        return None

    PART_ID = info['IDENTYFIKATOR'] + info[u'P\u0141EC'] + info['WIEK']
    logging.info('FRAME RATE: {}'.format(FRAME_RATE))
    logging.info('SCREEN RES: {}'.format(SCREEN_RES.values()))

    fix_cross = visual.TextStim(win, text='+', height=100, color=conf['FIX_CROSS_COLOR'])
    que = visual.Circle(win, radius=conf['QUE_RADIUS'], fillColor=conf['QUE_COLOR'], lineColor=conf['QUE_COLOR'])
    stim = visual.TextStim(win, text='', height=conf['STIM_SIZE'], color=conf['STIM_COLOR'])

    # mask = visual.ImageStim(win, image='mask2.png', size=(conf['STIM_FRAME_SIZE'], conf['STIM_FRAME_SIZE']),
    #                         pos=[conf['STIM_RECT_SHIFT'], 0])
    separator = [' ' * conf['REACTION_KEYS_SEP']] * len(conf['REACTION_KEYS'])
    question_frame = visual.TextStim(win, text="".join(["".join(x) for x in zip(conf['STIM_LETTERS'], separator)]), height=30,
                                     pos=(100, -300), color=conf['FIX_CROSS_COLOR'], wrapWidth=10000)
    question_label = visual.TextStim(win, text="".join(["".join(x) for x in zip(conf['REACTION_KEYS'], separator)]),
                                     height=30, pos=(100, -330), color=conf['FIX_CROSS_COLOR'], wrapWidth=10000)
    trial_no = 1
    # === Training ===

    show_info(win, join('.', 'messages', 'hello.txt'))
    show_info(win, join('.', 'messages', 'before_training.txt'))

    csi_list = [conf['TRAINING_CSI']] * conf['NO_TRAINING_TRIALS']
    for csi in csi_list:
        key_pressed, rt, stim_letter, choice, corr = run_trial(win, conf, fix_cross, csi, que, stim, clock, question_frame, question_label)
        RESULTS.append([PART_ID, trial_no, 'training', csi, stim_letter, key_pressed, choice, rt, corr])
        trial_no += 1

        # === Experiment ===

    show_info(win, join('.', 'messages', 'before_experiment.txt'))
    for _ in range(conf['NO_BLOCKS']):
        for _ in range(conf['INTRA_BLOCK_TRAINIG']):
            csi = random.choice(range(conf['CSI_BAND'][0], conf['CSI_BAND'][1]+1))
            key_pressed, rt, stim_letter, choice, corr = run_trial(win, conf, fix_cross, csi, que, stim, clock, question_frame, question_label)
            RESULTS.append([PART_ID, trial_no, 'training', csi, stim_letter, key_pressed, choice, rt, corr])
            trial_no += 1
        
        csi_list = list(range(conf['CSI_BAND'][0], conf['CSI_BAND'][1]+1))
        random.shuffle(csi_list)

        for csi in csi_list:
            key_pressed, rt, stim_letter, choice, corr = run_trial(win, conf, fix_cross, csi, que, stim, clock, question_frame, question_label)
            RESULTS.append([PART_ID, trial_no, 'experiment', csi, stim_letter, key_pressed, choice, rt, corr])
            trial_no += 1
        show_info(win, join('.', 'messages', 'break.txt'))

        # === Cleaning time ===
    save_beh_results()
    logging.flush()
    show_info(win, join('.', 'messages', 'end.txt'))
    win.close()


def run_trial(win, conf, fix_cross, CSI, que, stim, clock, question_frame, question_label):
    
    que_pos = random.choice([-conf['STIM_SHIFT'], conf['STIM_SHIFT']])
    stim.pos = [-que_pos, 0] # always on the other site
    stim.text = random.choice(conf['STIM_LETTERS'])

    for _ in range(conf['FIX_CROSS_TIME']):
        fix_cross.draw()
        win.flip()
    for _ in range(CSI):
        win.flip()
    
    for _ in range(conf['QUE_FREQ']):
        if _ % 2 == 0:
            que.pos = [que_pos + conf['QUE_SHIFT'], 0]
        else:
            que.pos = [que_pos - conf['QUE_SHIFT'], 0]
        for _ in range(conf['QUE_SPEED']):
            que.draw()
            win.flip()
    for _ in range(conf['STIM_TIME']):
        stim.draw()
        win.flip()

    question_frame.draw()
    question_label.draw()
    win.callOnFlip(clock.reset)
    win.flip()
    reaction = event.waitKeys(keyList=list(conf['REACTION_KEYS']), maxWait=conf['REACTION_TIME']/60, timeStamped=clock)
    if reaction:
        key_pressed, rt = reaction[0]
        choice = dict(zip(conf['REACTION_KEYS'], conf['STIM_LETTERS']))[key_pressed]
        corr = stim.text == choice
    else:
        key_pressed = 'no_key'
        rt = -1.0
        corr = 'no_ans'
        choice = 'no_letter'

    return key_pressed, rt, stim.text, choice, corr

if __name__ == '__main__':
    PART_ID = ''
    SCREEN_RES = get_screen_res()
    main()
