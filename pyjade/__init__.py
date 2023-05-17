# 恶意用户输入 username = "admin' OR 1=1"
query = "SELECT * FROM users WHERE username = '{0}'".format(username)
cursor.execute(query)

