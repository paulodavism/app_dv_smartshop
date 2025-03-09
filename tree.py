import os

def generate_tree(path, indent='', output_file=None):
    items = os.listdir(path)
    for i, item in enumerate(items):
        item_path = os.path.join(path, item)
        if os.path.isfile(item_path):
            output_file.write(indent + '├── ' + item + '\n')
        elif os.path.isdir(item_path):
            output_file.write(indent + '├── ' + item + '/\n')
            if i == len(items) - 1:
                generate_tree(item_path, indent + '    ', output_file)
            else:
                generate_tree(item_path, indent + '|   ', output_file)

project_path = '.'  # Caminho do projeto (diretório atual)
output_file_path = 'estrutura_projeto.txt'  # Nome do arquivo de saída

with open(output_file_path, 'w', encoding='utf-8') as output_file:
    output_file.write(os.path.basename(project_path) + '/\n')
    generate_tree(project_path, output_file=output_file)

print(f"Estrutura do projeto escrita em '{output_file_path}'")