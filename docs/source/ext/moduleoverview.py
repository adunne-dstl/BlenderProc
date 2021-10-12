from docutils.parsers.rst import Directive
from docutils import nodes
import pdb
from collections import defaultdict
from sphinx import addnodes
from pathlib import Path

class classlist(nodes.General, nodes.Element):
    pass


class ClasslistDirective(Directive):

    def run(self):
        return [classlist('')]

def generate_classlist(app, fromdocname, subtree, class_list, prefix, level=2):
    for e in class_list:
        ref = nodes.reference('', '')
        ref['refdocname'] = e[3]
        ref['refuri'] = app.builder.get_relative_uri(fromdocname, e[3])
        ref['refuri'] += '#' + e[4]
        ref.append(nodes.Text(prefix + e[0].split(".")[-1]))
        class_item = nodes.list_item('', addnodes.compact_paragraph('', '', ref), classes=["toctree-l" + str(level)])
        #print(fromdocname, e[3])
        if fromdocname.startswith(e[3].replace(".api.", ".")):
            #print("current")
            class_item['classes'].append('current')
        subtree += class_item

def generate_collapsible_classlist(app, fromdocname, classes, container, caption, module_index, label_prefix):
    toc = nodes.bullet_list()
    toc += nodes.caption(caption, '', *[nodes.Text(caption)])

    if module_index is not None:
        entries = defaultdict(list)
        #print("test", classes, fromdocname, caption)
        prefix = ".".join(classes[0][0].split(".")[:module_index]) + "."
        for e in classes:
            module = e[0].split(".")[module_index]
            entries[module].append(e)

        #print("t", fromdocname)
        for module, class_list in entries.items():
            #print("t2", "src." + prefix + module)
            ref = nodes.reference('', '')
            ref['refuri'] = app.builder.get_relative_uri(fromdocname, prefix + module)
            ref.append(nodes.Text((label_prefix + module) if label_prefix != "" else module.capitalize()))
            module_item = nodes.list_item('', addnodes.compact_paragraph('', '', ref), classes=["toctree-l1"])
            if fromdocname.startswith(prefix + module):
                module_item["classes"].append('current')
            toc += module_item

            subtree = nodes.bullet_list()
            module_item += subtree

            generate_classlist(app, fromdocname, subtree, class_list, "")
    else:
        generate_classlist(app, fromdocname, toc, classes, label_prefix, level=1)
    container += toc

def generate_examples_sidebar(app, fromdocname, container):
    examples = Path(__file__).absolute().parent.parent / "examples"

    container += nodes.caption("Examples", '', *[nodes.Text("Examples")])
    for example_groups in [examples / group for group in ["basics", "advanced", "datasets"]]:
        if example_groups.is_dir():
            toc = nodes.bullet_list()

            ref = nodes.reference('', '')
            ref['refuri'] = app.builder.get_relative_uri(fromdocname, "examples/" + example_groups.name + "/README")
            ref.append(nodes.Text(example_groups.name.capitalize()))
            module_item = nodes.list_item('', addnodes.compact_paragraph('', '', ref), classes=["toctree-l1"])
            if fromdocname.startswith("examples/" + example_groups.name):
                module_item["classes"].append('current')
            toc += module_item

            subtree = nodes.bullet_list()
            module_item += subtree

            for example in sorted(example_groups.rglob("*/README.md"), key=lambda x: x.parent.name):
                ref = nodes.reference('', '')
                ref['refuri'] = app.builder.get_relative_uri(fromdocname, str(example).replace(str(examples), "examples").replace("README.md", "README"))
                ref.append(nodes.Text(example.parent.name))
                class_item = nodes.list_item('', addnodes.compact_paragraph('', '', ref), classes=["toctree-l2"])

                if fromdocname == ref['refuri'].replace(".html", ""):
                    class_item['classes'].append('current')
                subtree += class_item

            container += toc

def generate_sidebar(app, fromdocname):
    env = app.builder.env
    container = nodes.compound(classes=['toctree-wrapper'])#addnodes.compact_paragraph('', '', classes=['toctree-wrapper'])
    py = env.get_domain('py')
    classes = py.get_objects()
    #print("classes", classes, [_[2] for _ in py.get_objects()])

    classes_per_group = {"api": ([], None, "bproc."), "internal": ([], 2, "bproc.python."), "modules (deprecated)": ([], 3, "")}#"modules": ([], 1), "provider": ([], 2),
    for e in classes:
        if e[2] == 'module' and e[3].startswith("blenderproc.api.") or e[2] == 'class' and not e[3].startswith("blenderproc.api."):
            #print(e)
            if e[3].startswith("blenderproc.api."):
                group = "api"
            elif e[0].startswith("blenderproc.python.modules."):
                group = "modules (deprecated)"
            else:
                group = "internal"
            #print(group, e)

            classes_per_group[group][0].append(e)

    generate_examples_sidebar(app, fromdocname, container)
    for key, items in classes_per_group.items():
        generate_collapsible_classlist(app, fromdocname, items[0], container, key.capitalize(), items[1], items[2])

    return container

def process_classlist(app, doctree, fromdocname):
    container = generate_sidebar(app, fromdocname)

    ctx = app.env.config['html_context']
    ctx['classlist'] = container
    for node in doctree.traverse(classlist):
        node.replace_self([container])
        continue


def add_classlist_handler(app):
    def _print_classlist(**kwargs):
        ctx = app.env.config['html_context']
        return app.builder.render_partial(ctx['classlist'])['fragment']

    ctx = app.env.config['html_context']
    if 'print_classlist' not in ctx:
        ctx['print_classlist'] = _print_classlist

def html_page_context(app, pagename, templatename, context, doctree):
    def make_toctree(collapse=True, maxdepth=-1, includehidden=True, titles_only=False):
        if "page_source_suffix" in context and context["page_source_suffix"] == ".md":
            fromdocname = context["current_page_name"]
        else:
            fromdocname = "" if "title" not in context else context["title"]

        fulltoc = generate_sidebar(app, fromdocname)
        rendered_toc = app.builder.render_partial(fulltoc)['fragment']
        return rendered_toc

    context['toctree'] = make_toctree

def setup(app):
    app.add_node(classlist)
    app.add_directive('classlist', ClasslistDirective)
    app.connect('doctree-resolved', process_classlist)
    app.connect('builder-inited', add_classlist_handler)
    app.connect('html-page-context', html_page_context)
