Require an API key to hit the backend API
    - Add API key management page
    - Create system API key, generated on first seed (unique per Dora instance) into the DB
    - Share between Dora API and Merchant API, or get them to generate their own
    - Probably want to disallow people using the Merchant API directly, block this by making separate key
    - Required to be sent as header in requests
    - Refresh?
    - Generate random key on init of DB, maybe through migration script?
