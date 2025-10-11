f = open('command.txt', 'r')
cli_list = f.readlines()

for i in cli_list:
    print(i)