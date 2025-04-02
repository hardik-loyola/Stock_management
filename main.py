import sqlite3
import PySimpleGUI as sg
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

try:
    conn = sqlite3.connect('investments.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
        company_name VARCHAR(255) PRIMARY KEY NOT NULL,
        price REAL NOT NULL ,
        quantity INTEGER NOT NULL
    )
    ''')
    conn.commit()
    cursor.execute('''    
        CREATE TABLE IF NOT EXISTS purchases (
            company_name VARCHAR(255) NOT NULL,
            purchase_date TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY (company_name) REFERENCES stocks (company_name)
        )
    ''')
    conn.commit()

    def custom_popup(message, title, auto_close_duration):
        layout = [[sg.Text(message, text_color="darkblue", font=("Helvetica", 20))]]
        win = sg.Window(title, layout, finalize=True, keep_on_top=True, no_titlebar=True, grab_anywhere=False, margins=(0, 0), alpha_channel=0.9)
        win.read(timeout=auto_close_duration)
        win.close()

    def add_company():
        win.hide()
        layout = [[sg.Text("Enter company name:")],
                [sg.Input(key="company_name")],
                [sg.Text("Enter price of per unit stock:")],
                [sg.Input(key="price")],
                [sg.Text("Enter stock quantity:")],
                [sg.Input(key="quantity")],
                [sg.Text("Enter purchase date:")],
                [sg.Input(key="purchase_date", visible=True), sg.CalendarButton("Select date", target="purchase_date", format="%Y-%m-%d", key="_CALENDAR_")],
                [sg.Button("Add company"), sg.Button("Back")]]

        window = sg.Window("Add new company", layout)

        while True:
            event, values = window.read()

            if event == "_CALENDAR_":
                window["purchase_date"].update(values[event])
                window["selected_date"].update(values[event])

            if event == "Add company":
                company_name = values["company_name"]
                price = values.get("price", "")
                quantity = values["quantity"]
                purchase_date = values["purchase_date"]

                if not company_name or not price or not quantity or not purchase_date:
                    sg.popup("Please fill in all fields.",title="")
                    continue

                try:
                    price = float(price)
                except ValueError:
                    sg.popup("Please enter a valid price.", title="Error")
                    continue

                try:
                    cursor.execute("SELECT COUNT(*) FROM stocks WHERE company_name = ?", (company_name,))
                    if cursor.fetchone()[0] > 0:
                        sg.popup("Company already exists in the database.", title="Error", auto_close_duration=600)
                        window.close()
                        win.un_hide()
                        break

                    cursor.execute("INSERT INTO stocks (company_name, price, quantity) VALUES (?, ?, ?)", (company_name, price, quantity))
                    cursor.execute("INSERT INTO purchases (company_name, purchase_date, price, quantity) VALUES (?, ?, ?, ?)", (company_name, purchase_date, price, quantity))
                    conn.commit()

                    custom_popup(f"Company '{company_name}' added successfully.", title="Company added", auto_close_duration=500)
                    window.close()
                    win.un_hide()
                    break
                except sqlite3.Error as e:
                    sg.popup(f"Error: {e}", title="SQLite Error")
                    break

            if event == sg.WIN_CLOSED or event == "Back":
                window.close()
                win.un_hide()
                break

        window.close()

    def company():
        win.hide()
        cursor.execute("SELECT company_name FROM stocks")
        companies = [row[0] for row in cursor.fetchall()]

        layout = [[sg.Text("Enter company name:")],
                [sg.Combo(companies, key="company_name", expand_x=True)],
                [sg.Text("Enter price per unit stock:")],
                [sg.Input(key="price", expand_x=True)],
                [sg.Text("Enter quantity:")],
                [sg.Input(key="quantity", expand_x=True)],
                [sg.Text("Enter purchase date:")],
                [sg.Input(key="purchase_date", visible=True), sg.CalendarButton("Select date", target="purchase_date", format="%Y-%m-%d", key="_CALENDAR_")],
                [sg.Button("Add purchase"), sg.Button("Back")]]

        window = sg.Window("Add stocks to existing company", layout)

        while True:
            event, values = window.read()

            if event == "_CALENDAR_":
                window["purchase_date"].update(values[event])

            if event == "Add purchase":
                company_name = values["company_name"]
                price = values["price"]
                quantity = values["quantity"]
                purchase_date = values["purchase_date"]

                if not company_name or not price or not quantity or not purchase_date:
                    sg.popup("Please fill in all fields.",title="Error")
                    continue

                try:
                    price = float(price)
                except ValueError:
                    sg.popup("Price should be in numbers",title="Error")
                    continue

                try:
                    cursor.execute("SELECT COUNT(*) FROM stocks WHERE company_name = ?", (company_name,))
                    if cursor.fetchone()[0] == 0:
                        sg.popup("This company does not exist in the database.")
                        continue

                    cursor.execute("UPDATE stocks SET price = ?, quantity = quantity + ? WHERE company_name = ?", (price, quantity, company_name))
                    cursor.execute("INSERT INTO purchases (company_name, purchase_date, price, quantity) VALUES (?, ?, ?, ?)", (company_name, purchase_date, price, quantity))
                    conn.commit()

                    custom_popup("Purchase added successfully.", title="Error", auto_close_duration=500)
                    window.close()
                    win.un_hide()
                    break
                except sqlite3.Error as e:
                    sg.popup(f"Error: {e}", title="SQLite Error")
                    break

            if event == sg.WIN_CLOSED or event == "Back":
                window.close()
                win.un_hide()
                break

        window.close()

    def show():
        win.hide()
        try:
            cursor.execute("""        
                SELECT
                    company_name,
                    quantity,
                    (SELECT price FROM purchases p WHERE p.company_name = s.company_name AND p.purchase_date = (SELECT MAX(purchase_date) FROM purchases p WHERE p.company_name = s.company_name)) AS current_price,
                    quantity * (SELECT price FROM purchases p WHERE p.company_name = s.company_name AND p.purchase_date = (SELECT MAX(purchase_date) FROM purchases p WHERE p.company_name = s.company_name)) AS total_price
                FROM
                    stocks s
            """ )
            stocks_data = cursor.fetchall()

            layout = [[sg.Table(values=stocks_data, headings=["Company name", "Quantity", "Current Price per stock", "Total Price"], max_col_width=20, auto_size_columns=True, justification="center", num_rows=min(len(stocks_data), 10))]]
            layout.append([sg.Button("Back", key="exit",  pad=(10, 10))])

            window = sg.Window("All records", layout, element_justification="center", size=(550, 300))

            while True:
                event, _ = window.read()
                if event == "exit" or event == sg.WIN_CLOSED:
                    win.un_hide()
                    break
        except sqlite3.Error as e:
            sg.popup(f"Error: {e}", title="SQLite Error")
        finally:
            window.close()

    def sell():
        win.hide()
        try:
            cursor.execute("""        
                SELECT
                    company_name,
                    quantity,
                    (SELECT price FROM purchases p WHERE p.company_name = s.company_name AND p.purchase_date = (SELECT MAX(purchase_date) FROM purchases p WHERE p.company_name = s.company_name)) AS current_price,
                    quantity * (SELECT price FROM purchases p WHERE p.company_name = s.company_name AND p.purchase_date = (SELECT MAX(purchase_date) FROM purchases p WHERE p.company_name = s.company_name)) AS total_price
                FROM
                    stocks s
            """ )
            stocks_data = cursor.fetchall()

            layout = [
                [sg.Button("Select ", key="select", pad=(10, 10)), sg.Text("", key="message", text_color="darkred", font=("Helvetica", 14))],
                [sg.Table(values=stocks_data, headings=["Company", "Quantity", "Current Price per stock", "Total Price"], max_col_width=20, auto_size_columns=True, justification="center", num_rows=min(len(stocks_data), 10), select_mode=sg.TABLE_SELECT_MODE_BROWSE, key="-TABLE-")],
                [sg.Button("Back", key="Back", pad=(10, 10))]
            ]

            window = sg.Window("Sell stocks", layout, element_justification="center", size=(500, 300))

            while True:
                event, values = window.read()

                if event == "select":
                    if "-TABLE-" not in values:
                        sg.popup("Please select a company to sell its stock.", title="Error")
                        continue

                    selected_rows = values["-TABLE-"]
                    if not selected_rows:
                        sg.popup("Please select a company to sell its stock.", title="Error")
                        continue

                    company_name = stocks_data[selected_rows[0]][0]
                    current_quantity = stocks_data[selected_rows[0]][1]

                    layout_sell = [[sg.Text("Current quantity of stocks:"), sg.Text(str(current_quantity), key="current_quantity", text_color="White", font=("Helvetica", 14))],
                                [sg.Text("Enter quantity to sell:")],
                                [sg.Input(key="sell_quantity", size=(10, 1))],
                                [sg.Button("Sell")],[sg.Text("OR")],[ sg.Button("Sell All"), sg.Button("Cancel")]]

                    window_sell = sg.Window("Sell stocks", layout_sell, element_justification="center", size=(400, 160))

                    while True:
                        event_sell, values_sell = window_sell.read()

                        if event_sell == "Sell":
                            sell_quantity = int(values_sell["sell_quantity"])
                            if sell_quantity <= 0:
                                sg.popup("Please enter a valid quantity to sell.", title="Error")
                                continue

                            if sell_quantity > current_quantity:
                                sg.popup(f"Insufficient quantity of stocks available for {company_name}.", title="Error")
                                continue

                            new_quantity = current_quantity - sell_quantity
                            cursor.execute("UPDATE stocks SET quantity = ? WHERE company_name = ?", (new_quantity, company_name))
                            conn.commit()

                            updated_stocks_data = [(row[0], new_quantity, row[2], row[3]) if row[0] == company_name else row for row in stocks_data]
                            window["-TABLE-"].update(values=updated_stocks_data)

                            custom_popup(f"{sell_quantity} stocks of {company_name} have been sold.", title="Stocks Sold", auto_close_duration=1000)

                            window_sell.close()
                            break

                        elif event_sell == "Sell All":
                            cursor.execute("DELETE FROM stocks WHERE company_name = ?", (company_name,))
                            conn.commit()

                            cursor.execute("DELETE FROM purchases WHERE company_name = ?", (company_name,))
                            conn.commit()

                            custom_popup(f"All the stocks of {company_name} have been sold/removed.", title="Stocks Sold", auto_close_duration=500)

                            window_sell.close()
                            break

                        elif event_sell == "Cancel":
                            window_sell.close()
                            break

                        elif event_sell == sg.WIN_CLOSED:
                            window_sell.close()
                            break

                    if event_sell in ["Sell", "Sell All"]:
                        window.close()
                        win.un_hide()
                        break

                elif event == sg.WIN_CLOSED or event == "Back":
                    window.close()
                    win.un_hide()
                    break

            window.close()
            win.un_hide()
        except sqlite3.Error as e:
            sg.popup(f"Error: {e}", title="SQLite Error")
        finally:
            window.close()
            win.un_hide()

    def graph():
        win.hide()
        try:
            cursor.execute("SELECT company_name FROM stocks")
            companies = [row[0] for row in cursor.fetchall()]

            layout = [[sg.Text("Select company:")],
                    [sg.Combo(companies, key="company_name", readonly=True)],
                    [sg.Button("Graph"), sg.Button("Back")],
                    [sg.Canvas(key='plot_canvas')]]

            size = (800, 500)

            window = sg.Window("Graph stock", layout, finalize=True, size=size)

            while True:
                event, values = window.read()

                if event == "Graph":
                    company_name = values["company_name"]

                    if not company_name:
                        sg.popup("Please select a company.", title="Error")
                        continue

                    cursor.execute("SELECT purchase_date, price FROM purchases WHERE company_name = ?", (company_name,))
                    data = cursor.fetchall()

                    if not data:
                        sg.popup("No data found for this company.", title="Error")
                        continue

                    dates = [row[0] for row in data]
                    prices = [row[1] for row in data]

                    fig, ax = plt.subplots(figsize=(12, 9)) 
                    ax.plot(dates, prices, marker='o')
                    ax.set_xlabel('Purchase Date')
                    ax.set_ylabel('Price')
                    ax.set_title(f'{company_name} Stock Price Over Time')

                    canvas_elem = window['plot_canvas'].TKCanvas
                    fig_canvas_agg = FigureCanvasTkAgg(fig, master=canvas_elem)
                    fig_canvas_agg.draw()
                    fig_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

                if event == sg.WIN_CLOSED or event == "Back":
                    window.close()
                    win.un_hide()
                    break
        except sqlite3.Error as e:
            sg.popup(f"Error: {e}", title="SQLite Error")
        finally:
            window.close()
            win.un_hide()

    def stocks():
        win.hide()
        try:
            layout = [[sg.Button("Back", key="back", pad=(10, 10))],
                    [sg.Canvas(key='plot_canvas')]]

            window = sg.Window("Compare Stocks", layout, finalize=True, size=(700, 500))

            cursor.execute("""
                SELECT
                    p.company_name,
                    p.purchase_date,
                    p.price
                FROM
                    stocks s
                    JOIN purchases p ON s.company_name = p.company_name
                ORDER BY
                    p.purchase_date
            """)
            data=cursor.fetchall()
            

            if not data:
                sg.popup("No data found for any companies.", title="Error")
                return

            companies = [row[0] for row in data]
            company_names = list(set(companies))
            prices = [row[2] for row in data]
            purchase_dates = [row[1] for row in data]

            unique_companies = list(set(companies))
            colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k']

            fig, ax = plt.subplots(figsize=(30, 10))

            for i, company in enumerate(unique_companies):
                indices = [j for j, x in enumerate(companies) if x == company]
                sorted_indices = sorted(indices, key=lambda idx: purchase_dates[idx])  # Sort indices by purchase date
                sorted_prices = [prices[idx] for idx in sorted_indices]
                sorted_dates = [purchase_dates[idx] for idx in sorted_indices]
                ax.plot(sorted_dates, sorted_prices, marker='o', label=company, color=colors[i % len(colors)])

            ax.set_xlabel('Purchase Date')
            ax.set_ylabel('Price')
            ax.set_title('Stock Prices Over Time')
            ax.legend()

            canvas_elem = window['plot_canvas'].TKCanvas
            fig_canvas_agg = FigureCanvasTkAgg(fig, master=canvas_elem)
            fig_canvas_agg.draw()
            fig_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)

            while True:
                event, values = window.read()

                if event == "back" or event == sg.WIN_CLOSED:
                    window.close()
                    win.un_hide()
                    break
        except sqlite3.Error as e:
            sg.popup(f"Error: {e}", title="SQLite Error")
        finally:
            window.close()

    lay1 = [[sg.Column([[sg.Button('Add new company', pad=(10), expand_x=True, tooltip="Click this button if you want to enter details for a new stock investment, including the company name, number of shares, purchase price, and the date of purchase.")],
                        [sg.Button('Add stocks to existing company', pad=(10), expand_x=True, tooltip='Click this button if you are purchasing additional stocks for a company you have previously invested in')],
                        [sg.Button('Show all stocks', pad=(10), expand_x=True, tooltip='Click this button to display a list of all the stock investments you have entered, including details for each company.')],
                        [sg.Button('Graph stock', pad=(10), expand_x=True, tooltip='Click this button to generate a graphical representation that displays how the stock price of a selected company has fluctuated over time.')],
                        [sg.Button('Compare stocks', pad=(10), expand_x=True, tooltip='Click this button to graphically compare the stock price trends over time for all the companies in the database')],
                        [sg.Button('Sell stocks', pad=(10), expand_x=True, tooltip="Click this button to sell either a specified quantity of stocks or to sell your entire stock of a specified company")]], justification='center')],
                        [sg.Column([[sg.Button(' Exit ',key='Exit', pad=(10), expand_x=True, tooltip='Close the application')]], justification='right')]]

    win = sg.Window("Welcome to Subedi's investments", lay1,  element_justification="center",size=(500,325))
    while True:
        event, values = win.read()
        if event==sg.WIN_CLOSED or event=='Exit':
            custom_popup("  BYE  ", title="Signup", auto_close_duration=400)
            break
        elif event=='Add new company':
            add_company()
        elif event=="Add stocks to existing company":
            company()
        elif event=="Show all stocks":
            show()
        elif event=='Graph stock':
            graph()
        elif event=='Compare stocks':
            stocks()
        elif event=="Sell stocks":
            sell()

    win.close()
except sqlite3.Error as e:
    sg.popup(f"Error: {e}", title="SQLite Error")
