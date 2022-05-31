import os, shutil
from utils.supervisor_utils import SONS, STATUS
import uuid

HTML_HEADER = '<!DOCTYPE html>' \
              '<html lang="en">' \
              '<head><meta charset="UTF-8">' \
              '<link rel= "stylesheet" type= "text/css" href= "{{ url_for(\'static\',filename=\'styles/treeStyle.css\') }}">' \
              '</head><body><div class="tree">'
HTML_FOOTER = '</div></body></html>'
NODE_HTML_OPEN = "<li>"
NODE_HTML_CLOSE = "</li>"


def delete_file():
    folder = 'templates/'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def get_html_node_structure(tree, node_id, status=''):
    status_html = f'<br/>{status}'
    tree_structure_html = NODE_HTML_OPEN + '<a>' + f'{node_id}{status_html}' + '</a>'
    if node_id in tree:
        if len(tree[node_id][SONS]) > 0:
            tree_structure_html += "<ul>"
        for son_id in tree[node_id][SONS]:
            status_son = tree[node_id][SONS][son_id][STATUS]
            tree_structure_html += get_html_node_structure(tree, son_id, status_son)
        if len(tree[node_id][SONS]) > 0:
            tree_structure_html += "</ul>"
    tree_structure_html += NODE_HTML_CLOSE
    return tree_structure_html


def generate_tree(tree, root_id):
    os.makedirs(os.path.dirname('templates/'), exist_ok=True)
    delete_file()  # delete previous file if exists
    temp_file_name = 'tree_html_' + str(uuid.uuid4())
    tree_page = HTML_HEADER + ('<ul>' + get_html_node_structure(tree, root_id) + '</ul>' if len(
        tree.keys()) > 0 else '<p> Empty Tree </p>') + HTML_FOOTER
    tree_html = open(f"templates/{temp_file_name}.html", "w+")
    tree_html.write(tree_page)
    tree_html.close()
    return temp_file_name
