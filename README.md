# ISE Guest Management Bot

Code sample used to demo a webex teams bot that can create/add/delete ISE Guest users

## Usage

Within the script, there is a "Required Fields" section, where you will need to provide the following information:

**BOT_APP_NAME, BOT_EMAIL, ACCESS_TOKEN, BOT_ID:** Fill in with the info provided when creating a Webex Teams bot here: https://developer.webex.com/my-apps
**BOT_URL:** URL for Webex teams callbacks

**ISE_USER, ISE_PW:** ISE credentials for the API account, which will be used to manage guest users

**ISE_URL:** URL to the ISE ERS page (ex. https://192.168.1.1:9060/ers)

**portalID:** Enter the ID for the guest sponsor portal that will be managed