*** Settings ***

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers

*** Test Cases ***

Manager can edit the user schema
    Given I'm logged in as a 'Manager'
     then I can go to Member fields editor
     and I can add a new field
     and I can see this new field in user form

*** Keywords ***

I'm logged in as a '${ROLE}'
    Enable autologin as  ${ROLE}

I can go to Member fields editor
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link  link=Users and Groups
    Click link  link=Member fields

I can add a new field
    Click button    css=#add-field input[type='submit']
    Wait Until Element Is visible  css=#add-field-form  timeout=5
    Input Text      css=#add-field-form #form-widgets-title    Office name
    Click button    css=#add-field-form input[name='form.buttons.add']

I can see this new field in user form
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link    css=a[title='test_user_1_']
    Element should be visible  css=input#form-widgets-office_name