def parse_websites(websites):
    with open(websites, 'r') as file:
        websites = file.readlines()
    return websites
