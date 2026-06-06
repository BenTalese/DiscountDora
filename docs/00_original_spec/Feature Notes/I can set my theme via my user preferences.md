---
description:
---
- theme name stored in DB, either in user directly or UserSetting (will probably have GlobalSetting)  
- User + Option = UserOption association table which holds a value, so: userID, optionID, value  
- creating a user will create a default set of options  
- use case to get options for a user (or the whole user?)