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
     and I can make it appear in user profile
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

I can make it appear in user profile
    Click link      css=div[data-field_id='office_name'] a.fieldSettings
    Wait Until Element Is visible  css=#edit-field-form  timeout=5
    Select Checkbox     css=#edit-field-form input[value='In User Profile']
    Select Checkbox     css=#edit-field-form input[value='On Registration']
    Click button        css=#edit-field-form input[name='form.buttons.save']

I can see this new field in user form
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link    css=a[title='test_user_1_']
    Element should be visible  css=input#form-widgets-office_name