import os
import random
import sqlite3
import time
import smtplib
from email.message import EmailMessage


script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, "checker.db")

connection = sqlite3.connect(db_path)
cursor = connection.cursor()


def send_reset_code(recipient_email, code):
    sender_email = "zakariatabbara611@gmail.com"
    app_password = "phen thfj ibga uhns"

    msg = EmailMessage()
    msg['Subject'] = "Your Password Reset Code"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg.set_content(f"Hello,\n\nYour 6-digit verification code is: {code}\n\nIf you did not request this, please ignore this email.")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
            print(f"\n Verification code sent to {recipient_email}!")
            return True
    except Exception as e:
        print(f"\n Failed to send email: {e}")
        return False


attempts = 0
max_attempts = 3

print("=== Welcome to GPA Calculator ===")
choice = input("Press 'l' to log in, 'c' to create an account, or 'f' for forgot password: ").lower().strip()

while choice not in ['l', 'c', 'f']:
    choice = input("Invalid choice. Enter 'l' to log in, 'c' to create, or 'f' for forgot password: ").lower().strip()


if choice == 'l':
    while attempts < max_attempts:
        username = input("\nWhat is your username? ").strip()
        password = input("What is your password? ").strip()

        cursor.execute("SELECT password FROM logen WHERE username = ?", (username,))
        result = cursor.fetchone()

        if result is not None and result[0] == password:
            print("\n You are logged in! Welcome to GPA Calculator.")
            break
        else:
            attempts += 1
            print(" Username or password is incorrect.")

        if attempts == max_attempts:
            print("\n Too many failed attempts!")
            reset_choice = input("Did you forget your password? (y/n): ").lower().strip()

            if reset_choice == 'y':
                cursor.execute("SELECT email FROM logen WHERE username = ?", (username,))
                user_record = cursor.fetchone()

                if user_record is None:
                    print(" Username not found in database!")
                else:
                    user_email = user_record[0]
                    code = str(random.randint(100000, 999999))

                    if send_reset_code(user_email, code):
                        user_input = input("\nEnter the 6-digit code sent to your email: ").strip()

                        if user_input == code:
                            new_password = input("Enter your new password: ").strip()
                            cursor.execute("UPDATE logen SET password = ? WHERE username = ?", (new_password, username))
                            connection.commit()
                            print(" Success! Your password has been updated. You can now log in.")
                            break
                        else:
                            print(" Invalid verification code.")

            print("\nAccount locked for 5 seconds...")
            time.sleep(5)
            attempts = 0
            print("Lock expired. You can try again now.\n")
        else:
            print(f"You have {max_attempts - attempts} attempt(s) left.")


elif choice == 'c':
    while True:
        username = input("\nChoose a username: ").strip()

        cursor.execute("SELECT username FROM logen WHERE username = ?", (username,))
        if cursor.fetchone() is not None:
            print(" That username is already taken, please choose another one.")
            continue

        email = input("Enter your email address: ").strip()

        cursor.execute("SELECT email FROM logen WHERE email = ?", (email,))
        if cursor.fetchone() is not None:
            print(" That email is already registered to another account!")
            continue

        password = input("Choose a password: ").strip()

        cursor.execute("INSERT INTO logen (username, password, email) VALUES (?, ?, ?)", (username, password, email))
        connection.commit()
        print("\n Account created successfully! You can now log in.")
        break


elif choice == 'f':
    username = input("\nEnter your username: ").strip()

    cursor.execute("SELECT email FROM logen WHERE username = ?", (username,))
    result = cursor.fetchone()

    if result is None:
        print(" Username not found!")
    else:
        user_email = result[0]
        code = str(random.randint(100000, 999999))

        if send_reset_code(user_email, code):
            user_input = input("\nEnter the 6-digit code sent to your email: ").strip()

            if user_input == code:
                new_password = input("Enter your new password: ").strip()
                cursor.execute("UPDATE logen SET password = ? WHERE username = ?", (new_password, username))
                connection.commit()
                print(" Success! Your password has been updated. You can now log in.")
            else:
                print(" Invalid verification code. Password reset canceled.")


connection.close()