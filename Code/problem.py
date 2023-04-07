tasks = []
for i in range(5):
    def action(x=i):
        print(str(x))
    tasks.append(action)

for task in tasks:
    task()