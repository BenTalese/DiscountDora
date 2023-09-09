# class UserDomainEntity:
#     def __init__(self, user_id, username, email):
#         self.user_id = user_id
#         self.username = username
#         self.email = email

# # Automatically parse incoming JSON into the framework model
# json_data = {"user_id": 1, "username": "john_doe", "email": "john@example.com"}
# user_model = UserModel(**json_data)

# # Convert the framework model to a domain entity
# user_domain_entity = UserDomainEntity(**user_model.dict())
