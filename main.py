import time, json, sys
from getpass import getpass
from os.path import exists
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from cryptography.fernet import Fernet

manifest_file = open('manifest.txt', 'r')
manifest_list = manifest_file.readlines()

with open('config.json') as config_file:
    conf = json.load(config_file)

settings = conf['settings']
element_paths = conf['element_paths']

creds = "\n\n*** Created by Missionloyd :) ***\nhttps://github.com/missionloyd\n"

time.sleep(1)

#credentials to LinkedIn
credential = {
    "username": None,
    "password": None
}

#ask user for credentials
def get_credential():
    print("Please fill in your credentials\n(Your info will encrypted, saved locally and will NOT be shared to ANYONE)\n")
    username = input("Email: ")
    password = getpass()
    print("\n")
    return username, password

#encrypt username and password
if(settings['save_credentials'] == True):
    if not exists("cred.enc"):

        #generate keys 
        key = Fernet.generate_key()
        cipher = Fernet(key)

        #load credentials encode/encrypt
        credential['username'], credential['password'] = get_credential()
        credential_byte = json.dumps(credential).encode('utf-8')
        cred_enc = cipher.encrypt(credential_byte)

        #save encoded credentials to a file and save key to seperate file
        with open("cred.enc", "wb") as f1, open("cred.key", "wb") as f2:
            f1.write(cred_enc)
            f2.write(key)

    #decrypt, open encoded credentials and open key
    with open("cred.enc", "rb") as f1, open("cred.key", "rb") as f2:
        cred_decrypt = f1.read()
        key = f2.read()
        cipher = Fernet(key)
        data = json.loads(cipher.decrypt(cred_decrypt).decode('utf-8'))

    #set username and password
    username = data["username"]
    password = data["password"]

else:
    username, password = get_credential()


def checkIfElementExists(name, form, driver):
    by = By.ID

    if(form == 'XPATH'):
        by = By.XPATH
    elif(form == "CLASS_NAME"):
        by = By.CLASS_NAME

    WebDriverWait(driver, settings['max_wait_time']).until(
        EC.presence_of_element_located((by, name))
    )

    return
#######################

#open firefox and login
#https://chromedriver.chromium.org/downloads
try:
    print("Opening...\n")

    driver = webdriver.Firefox()

    driver.get(settings['base_url'])
    
     # wait until security check is over
    while True:
        if(input('Ready? (y/N)\n') == 'y'):
            break
        else:
            driver.close()
            sys.exit()

except:
    print("\nError... Looks Like you do not have a Web Driver installed!\nOr the URL to the form has changed!")
    sys.exit()

#update user
print("\nSigning In...\n")

#send keys and sumbit login
try:
    checkIfElementExists(element_paths['sign_in_button'], 'XPATH', driver)
    driver.find_element_by_xpath(element_paths['sign_in_button']).click()
    print("*\n")
    driver.find_element_by_xpath(element_paths['username_field']).send_keys(username)
    print("*\n")
    driver.find_element_by_xpath(element_paths['password_field']).send_keys(password)
    print("*\n")
    driver.find_element_by_xpath(element_paths['sign_in_submit']).click()
    print("*\n")
except:
    print("\nError... Looks like we had trouble logging in...\nCheck credentials, driver file, manifest.txt format")
    driver.close()
    sys.exit()

print("Successful Sign In!\n")
count = 0

for new_connection_url in manifest_list:

    if(settings['max_accounts'] <= count): 
        break
    elif(len(new_connection_url) == 0):
        continue
    
    print("\n***Finding User[" + str(count) + "]***\n")
    time.sleep(2)

    # go to user's url
    try:
        driver.get(new_connection_url.rstrip())
        print("*\n")
        checkIfElementExists(element_paths['connect_container'], 'XPATH', driver)
    except:
        print("Had trouble getting to new user's page...")
        continue

    print("User Found!\n")
    # Extracting the Name
    try:
        checkIfElementExists('pv-text-details__left-panel', 'CLASS_NAME', driver)
        src = driver.page_source
        # Now using beautiful soup
        soup = BeautifulSoup(src, 'lxml')

        intro = soup.find('div', {'class': 'pv-text-details__left-panel'})
        name_loc = intro.find("h1")
        name = name_loc.get_text().strip().split(' ')[0].replace(" ", "")
    except:
        print("\nFailed to extract name")
        continue

    # Extracting the Name, Location
    try:
        checkIfElementExists('text-body-small', 'CLASS_NAME', driver)
        src = driver.page_source
        # Now using beautiful soup
        soup = BeautifulSoup(src, 'lxml')

        intro = soup.find('div', {'class': 'pv-text-details__left-panel'})

        # first extract name
        name_loc = intro.find("h1")
        name = str(name_loc.get_text().strip()).split(" ")[0].replace(",", "")

        works_at_loc = intro.find("div", {'class': 'text-body-medium'})

        # this gives us the HTML of the tag in which the Company Name is present
        # Extracting the Company Name
        works_at = works_at_loc.get_text().strip()

        details = soup.find('div', {'class': 'pb2 pv-text-details__left-panel'})

        location_loc = details.find_all("span", {'class': 'text-body-small'})

        # Ectracting the Location
        location = str(location_loc[0].get_text().strip()).split(" ")[0].replace(",", "")
    except:
        print("Failed to extract profile info")
        continue

    print("Attempting to Connect...\n")

    # try pressing connect button
    try:
        buttons = driver.find_elements_by_xpath(element_paths['connect_container'])
        print("*\n")
        driver.find_element_by_id(buttons[1].get_attribute("id")).click()
    except:
        print("Had trouble with connect button...")
        continue

    if(settings['send_message'] == True):
        # try sending a note
        try:
            checkIfElementExists(element_paths['add_note_container'], 'XPATH', driver)
            buttons = driver.find_elements_by_xpath(element_paths['add_note_container'])

            custom_message = "Hi there, " + name + "! Nice to see another ASU (current/former) student networking outside of class." + " Hope you are enjoying " + location + ". " + "Good luck with your endeavors and see you out in the field!"

            checkIfElementExists(buttons[0].get_attribute("id"), 'ID', driver)
            driver.find_element_by_id(buttons[0].get_attribute("id")).click()

            checkIfElementExists(element_paths['custom_message'], 'XPATH', driver)
            driver.find_element_by_xpath(element_paths['custom_message']).send_keys(custom_message)
            print("*\n")
        except:
            print("Had trouble with custom message...")
            continue


    # try pressing send button
    try:
        checkIfElementExists(element_paths['send_container'], 'XPATH', driver)
        buttons = driver.find_elements_by_xpath(element_paths['send_container'])
        print("*\n")
        driver.find_element_by_id(buttons[0].get_attribute("id")).click()
        count+=1
    except:
        print("Had trouble with connect button...")
        continue

    print("***Successful Connection #"+ str(count) +"!***\n")

try:
    print(creds)
    driver.close()
    sys.exit()
except:
    sys.exit()


#for finding the frame of the form
def switch_to_iFrame():
    frame = driver.find_element_by_xpath('/html/body/div[2]/div/div/div[2]/div/iframe')
    driver.switch_to.frame(frame)