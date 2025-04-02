import sqlite3
import PySimpleGUI as sg

conn = sqlite3.connect('investments.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
''')
conn.commit()

def custom_popup(message, title, auto_close_duration):
    layout = [[sg.Text(message, text_color="darkblue", font=("Helvetica", 20))]]
    win = sg.Window(title, layout, finalize=True, keep_on_top=True, no_titlebar=True, grab_anywhere=False, margins=(0, 0), alpha_channel=0.9)
    win.read(timeout=auto_close_duration)
    win.close()

def signup():
    win.hide()
    lay2=[[sg.Text("")],
        [sg.Text("")],
        [sg.Text("")],
        [sg.Column([
            [sg.Text("Username:", font=("Helvetica", 20)), sg.InputText(size=(30, 1), key='Uname')],
            [sg.Text("Password: ", font=("Helvetica", 20)), sg.InputText(size=(30, 1), key='pw', password_char='•')],
            [sg.Button('Submit', pad=(10), expand_x=True)],
            [sg.Button('Back',key="Exit", pad=(10), expand_x=True)]
        ], justification='center')],
        [sg.Text("")],
        [sg.Text("")]]
    
    win1=sg.Window('Sign Up Page', layout=lay2,size=(500,300)).Finalize()
    while True:
     event, values = win1.read()
     if event==sg.WIN_CLOSED or event=='Exit':
        custom_popup("Taking you back to the login page", title="Signup", auto_close_duration=750)
        break
     if event=='Submit':
        username = values['Uname']
        password = values['pw']
        if not username or not password:
            sg.popup("Please enter a username and password.", title="Error", auto_close_duration=1000)
            continue
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            custom_popup("Sign up successful!",  title="Success", auto_close_duration=1000)
            break
        except sqlite3.IntegrityError:
            sg.popup("Username already exists. Please choose a different username")
    
    win1.close()
    win.un_hide()
    return values

lay1 = [[sg.Text("")],
        [sg.Text("")],
        [sg.Text("")],
        [sg.Column([
            [sg.Text("Username:", font=("Helvetica", 20)), sg.InputText(size=(30, 1), key='Uname')],
            [sg.Text("Password: ", font=("Helvetica", 20)), sg.InputText(size=(30, 1), key='pw', password_char='•')],
            [sg.Button('Login', pad=(10), expand_x=True), sg.Button('Signup', pad=(10),  expand_x=True)],
            [sg.Button('Exit', pad=(10), expand_x=True)]
        ], justification='center')],
        [sg.Text("")],
        [sg.Text("")],]

win = sg.Window("Login Page", lay1,  element_justification="center",size=(500,300))

while True:
    event, values = win.read()
    if event==sg.WIN_CLOSED or event=='Exit':
        break
    if event=="Signup":
        custom_popup("The signup window is opening ", title="Signup", auto_close_duration=600)
        signup_values = signup()
        win.find_element('Uname').Update(signup_values['Uname'])
        
    if event=='Login':
        username = values['Uname']
        password = values['pw']

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        result = cursor.fetchone()
        if result: 
          win.close()
          custom_popup("Logged in successfully!", title="Success", auto_close_duration=600)
          import main
          
         
          
          
          
          
        else:  
         sg.popup("Invalid username or password.", title="Error", auto_close_duration=1000)
         win['Uname'].Update('')
         win['pw'].Update('')
win.close()
