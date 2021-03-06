import sys
import subprocess
import json

import PySimpleGUI as simple
import sounddevice as sound
import wavio

from utils.phraselate import import_questions, select_question

def record_query(fps):
    duration = 5.5
    query = sound.rec(int(duration*fps), samplerate=fps, channels=1)
    sound.wait()

    return query

def run_tts(filename, lang, debug=False):
    # Convert wav bits
    sox_filename = filename.split('.')[0] + '2.' + filename.split('.')[1]
    sox_command = ['sox', filename, '-b', '16', sox_filename]
    subprocess.run(sox_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Run tts with deepspeech
    if lang == 'english':
        command = ['deepspeech', '--model', './utils/deepspeech-0.7.3-models.pbmm', '--scorer', './utils/deepspeech-0.7.3-models.scorer', '--audio', sox_filename]
    else:
        command = ['deepspeech', '--model', './utils/esu_model_500epochs.pbmm', '--scorer', './utils/esu_lm.scorer', '--audio', sox_filename]
        
    process = subprocess.run(command, capture_output=True)
    if debug:
        print(process.stderr)
        print(process.stdout)
    output = process.stdout.decode()

    return output.strip()

def audio_to_question(filename, fps, lang, debug=False):
    query_audio = wavio.write(filename, record_query(fps), fps, sampwidth=3)
    
    if debug:
        query = run_tts(filename, lang, debug=True)
    else:
        query = run_tts(filename, lang)

    # Questions format per question: [score, lang_b_q, lang_b_ans, eng_q, eng_ans]
    questions = select_question(query.split(), import_questions(sys.argv[1]), lang)
    
    return questions

def main():
    questions = []
    with open(sys.argv[1], 'r') as question_file:
        faq = json.load(question_file)
        eng_compiled_faq = []
        esu_compiled_faq = []
        for q_num, q in faq.items():
            eng_compiled_faq += [q_num + ') ' + list(q[0].items())[0][0]]
            esu_compiled_faq += [q_num + ') ' + list(q[1].items())[0][0]]
        eng_faq = '\n'.join(eng_compiled_faq)
        esu_faq = '\n'.join(esu_compiled_faq)

    fps = 16000
    gui = [
    [simple.Text("Welcome! You can use this phraselator to search through the Alaska State government's frequently asked questions brochure regarding employee rights/benefits.\nThe Alaska State government's webpage where the FAQ is located can be found at https://labor.alaska.gov/lss/whfaq.htm.", font='25')],
    [simple.Text("If you aren't sure what you can ask, click here (whichever language you prefer) to see a listing of possible questions.", font='25'), simple.Button('English Questions', font='10'), simple.Button("Yup'ik Questions", font=10)],
    [simple.Text("Press the button below to record your question (in English),  and the system will find the closest question. You will have about 5 seconds to record your question.\nIf an appropriate question does not appear in the drop down once you submit, please submit again. If it does, select and confirm to receive the questions and answers.", font='25')],
    [simple.Text("Below you can choose wheter to search with Yup'ik or English speech.")],
    [simple.Radio('English', 'search_language', key='english', default='true', font='15'), simple.Radio("Yup'ik", 'search_language', key="yupik", font="15")],
    [simple.Button('Record', font='10')],
    [simple.Text('Please select a question...', font='25')],
    [simple.Combo([], key='questions', size=(35, 10), font='25'), simple.Button('Confirm', font='10')],
    [simple.Text("English", font='25'), simple.Text(("\t"*4)+(" "*18)+"Yup'ik", font='25')],
    [simple.Multiline("", key='english_q', size=(43, 1), font='25'), simple.Multiline("", key='langb_q', size=(43, 1), font='25')],
    [simple.Multiline("", size=(43, 5), key='english_ans', font='25'), simple.Multiline("", size=(43, 5), key='langb_ans', font='25')]
    ]

    app = simple.Window("Central Alaskan Yup'ik Phraselator", gui)
    
    while True:
        gui_event, values = app.read()
        if gui_event == simple.WIN_CLOSED:
            break
        elif gui_event == 'Record':
            lang = 'english' if values['english'] else 'yupik'
            if len(sys.argv) > 2:
                questions = audio_to_question('query.wav', fps, lang, debug=True)
            else:
                questions = audio_to_question('query.wav', fps, lang)
            q_lang = 3 if lang=='english' else 1
            app['questions'].update(values=[questions[0][1][q_lang], questions[1][1][q_lang]])
        elif gui_event == 'Confirm':
            for _, question in questions:
                if values['questions'] in question:
                    update_q = question
                    break
            
            app['english_q'].update(update_q[3])
            app['english_ans'].update(update_q[4])
            app['langb_q'].update(update_q[1])
            app['langb_ans'].update(update_q[2])
        elif gui_event == 'English Questions':
            simple.popup_scrolled(eng_faq, title='Question Listing', font='25')
        elif gui_event == "Yup'ik Questions":
            simple.popup_scrolled(esu_faq, title='Question Listing', font='25')
            
    app.close()

if __name__ == '__main__':
    main()
