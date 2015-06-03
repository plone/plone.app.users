*** Settings ***

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers

Suite setup  Set Selenium speed  0.5s

*** Test Cases ***

Manager can edit the user schema
    Given I'm logged in as a 'Manager'
     then I go to Member fields editor
     and I add a new Text line (String) field 'office_name'
     and I do not see the 'office_name' field in user form
     and I make 'office_name' field appear In User Profile form
     and I see the 'office_name' field in user form
     and I do not see the 'office_name' field in registration form
     and I make 'office_name' field appear On Registration form
     and I see the 'office_name' field in registration form
     and I make the 'office_name' field required

Fields order is honored
    Given I'm logged in as a 'Manager'
     then I add a new Text line (String) field 'office_name'
     and I make 'office_name' field appear In User Profile form
     and I make 'office_name' field appear On Registration form
     and I add a new Text line (String) field 'job_title'
     and I make 'job_title' field appear In User Profile form
     and I make 'job_title' field appear On Registration form
     and 'office_name' is before 'job_title' in registration form
     and 'office_name' is before 'job_title' in user profile

Requirement constraint is honored
    Given I'm logged in as a 'Manager'
     then I add a new Text line (String) field 'office_name'
     and I make 'office_name' field appear In User Profile form
     and 'office_name' is not required
     and I add a new Integer field 'favorite_star_wars_episode'
     and I make 'favorite_star_wars_episode' field appear In User Profile form
     and 'favorite_star_wars_episode' is not required
     and I make the 'office_name' field required
     and 'office_name' is required

Type constraint is honored
    Given I'm logged in as a 'Manager'
     and I add a new Integer field 'favorite_star_wars_episode'
     and I make 'favorite_star_wars_episode' field appear In User Profile form
     and 'favorite_star_wars_episode' cannot be IV
     and 'favorite_star_wars_episode' can be 5

Min/max constraint is honored
    Given I'm logged in as a 'Manager'
     and I add a new Integer field 'favorite_star_wars_episode'
     and I make 'favorite_star_wars_episode' field appear In User Profile form
     and I restrict 'favorite_star_wars_episode' value to min 4 and max 6
     and value 3 is too small for 'favorite_star_wars_episode'
     and value 10 is too big for 'favorite_star_wars_episode'
     and 'favorite_star_wars_episode' can be 5

*** Keywords ***

I'm logged in as a '${ROLE}'
    Enable autologin as  ${ROLE}

I go to Member fields editor
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link  link=Users and Groups
    Click link  link=Member fields

I add a new ${field_type} field '${field_id}'
    Go to  ${PLONE_URL}/@@member-fields
    Wait Until Element Is visible  css=#add-field  timeout=5
    Click link   css=#add-field
    Wait Until Element Is visible  css=#add-field-form  timeout=5
    Input Text      css=#add-field-form #form-widgets-title     ${field_id}
    Input Text      css=#add-field-form #form-widgets-__name__  ${field_id}
    Select From List    css=#form-widgets-factory   ${field_type}
    Click button        css=.pattern-modal-buttons input#form-buttons-add

I make '${field_id}' field appear ${FORM} form
    Go to  ${PLONE_URL}/@@member-fields
    Wait Until Element Is visible  css=div[data-field_id='${field_id}']  timeout=5
    Click link      css=div[data-field_id='${field_id}'] a.fieldSettings
    Wait Until Element Is visible  css=#edit-field-form  timeout=5
    Select Checkbox     css=#edit-field-form input[value='${FORM}']
    Click button        css=.pattern-modal-buttons input#form-buttons-save

I do not see the '${field_id}' field in user form
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link    css=a[title='test_user_1_']
    Element should not be visible  css=input#form-widgets-${field_id}

I see the '${field_id}' field in user form
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link    css=a[title='test_user_1_']
    Element should be visible  css=input#form-widgets-${field_id}

I do not see the '${field_id}' field in registration form
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click button    css=#add-new-user
    Wait Until Element Is visible   css=form.kssattr-formname-new-user
    Element should not be visible  css=input#form-widgets-${field_id}

I see the '${field_id}' field in registration form
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click button    css=#add-new-user
    Wait Until Element Is visible   css=form.kssattr-formname-new-user
    Element should be visible  css=input#form-widgets-${field_id}

I make the '${field_id}' field required
    Go to  ${PLONE_URL}/@@member-fields
    Wait Until Element Is visible  css=div[data-field_id='${field_id}']  timeout=5
    Click link      css=div[data-field_id='${field_id}'] a.fieldSettings
    Wait Until Element Is visible  css=#edit-field-form  timeout=5
    Select Checkbox     css=#form-widgets-required-0
    Click button        css=.pattern-modal-buttons input#form-buttons-save

'${field_1}' is before '${field_2}' in registration form
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click button    css=#add-new-user
    Wait Until Element Is visible   css=form.kssattr-formname-new-user
    Element should be visible  css=#formfield-form-widgets-${field_1} + #formfield-form-widgets-${field_2}

'${field_1}' is before '${field_2}' in user profile
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link    css=a[title='test_user_1_']
    Element should be visible  css=#formfield-form-widgets-${field_1} + #formfield-form-widgets-${field_2}

'${field_id}' is not required
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link      css=a[title='test_user_1_']
    Input Text      css=#form-widgets-fullname  Isaac Newton
    Input Text      css=#form-widgets-email  isaac@plone.org
    Click button    css=#form-buttons-save
    Wait Until Element Is visible   css=.portalMessage
    Page should not contain    Required input is missing

'${field_id}' is required
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link      css=a[title='test_user_1_']
    Input Text      css=#form-widgets-fullname  Isaac Newton
    Input Text      css=#form-widgets-email  isaac@plone.org
    Click button    css=#form-buttons-save
    Wait Until Element Is visible   css=.portalMessage
    Page should contain    Required input is missing

I restrict '${field_id}' value to min ${min_val} and max ${max_val}
    Go to  ${PLONE_URL}/@@member-fields
    Wait Until Element Is visible  css=div[data-field_id='${field_id}']  timeout=5
    Click link      css=div[data-field_id='${field_id}'] a.fieldSettings
    Wait Until Element Is visible  css=#edit-field-form  timeout=5
    Input Text      css=#form-widgets-min  ${min_val}
    Input Text      css=#form-widgets-max  ${max_val}
    Click button        css=.pattern-modal-buttons input#form-buttons-save

value ${value} is too small for '${field_id}'
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link      css=a[title='test_user_1_']
    Input Text      css=#form-widgets-fullname  Isaac Newton
    Input Text      css=#form-widgets-email  isaac@plone.org
    Input Text      css=#form-widgets-${field_id}  ${value}
    Click button    css=#form-buttons-save
    Wait Until Element Is visible   css=.portalMessage  timeout=5
    Page should contain    Value is too small

value ${value} is too big for '${field_id}'
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link      css=a[title='test_user_1_']
    Input Text      css=#form-widgets-fullname  Isaac Newton
    Input Text      css=#form-widgets-email  isaac@plone.org
    Input Text      css=#form-widgets-${field_id}  ${value}
    Click button    css=#form-buttons-save
    Wait Until Element Is visible   css=.portalMessage  timeout=5
    Page should contain    Value is too big

'${field_id}' can be ${value}
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link      css=a[title='test_user_1_']
    Input Text      css=#form-widgets-fullname  Isaac Newton
    Input Text      css=#form-widgets-email  isaac@plone.org
    Input Text      css=#form-widgets-${field_id}  ${value}
    Click button    css=#form-buttons-save
    Wait Until Element Is visible    css=.portalMessage  timeout=5
    Element should not be visible    css=.portalMessage.error

'${field_id}' cannot be ${value}
    Go to  ${PLONE_URL}/@@overview-controlpanel
    Click link      link=Users and Groups
    Click link      css=a[title='test_user_1_']
    Input Text      css=#form-widgets-fullname  Isaac Newton
    Input Text      css=#form-widgets-email  isaac@plone.org
    Input Text      css=#form-widgets-${field_id}  ${value}
    Click button    css=#form-buttons-save
    Wait Until Element Is visible   css=.portalMessage  timeout=5
    Element should be visible       css=.portalMessage.error
