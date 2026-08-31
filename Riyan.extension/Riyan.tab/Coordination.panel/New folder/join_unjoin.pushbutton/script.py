
import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from pyrevit import script, forms

# Get the current document
doc = __revit__.ActiveUIDocument.Document

# Function to get all model categories in use in the current model
def get_model_categories_in_use(doc):
    model_categories = set()
    for elem in FilteredElementCollector(doc).WhereElementIsNotElementType().ToElements():
        if elem.Category is not None and elem.Category.CategoryType == CategoryType.Model:
            model_categories.add(elem.Category.Name)
    return sorted(list(model_categories))

# Function to join elements
def join_elements(elements_to_join):
    with Transaction(doc, "Join Elements") as trans:
        trans.Start()
        for pair in elements_to_join:
            elem1, elem2 = pair
            if not JoinGeometryUtils.AreElementsJoined(doc, elem1, elem2):
                JoinGeometryUtils.JoinGeometry(doc, elem1, elem2)
        trans.Commit()

# Function to unjoin elements
def unjoin_elements(elements_to_unjoin):
    with Transaction(doc, "Unjoin Elements") as trans:
        trans.Start()
        for pair in elements_to_unjoin:
            elem1, elem2 = pair
            if JoinGeometryUtils.AreElementsJoined(doc, elem1, elem2):
                JoinGeometryUtils.UnjoinGeometry(doc, elem1, elem2)
        trans.Commit()

# Function to collect elements from user-selected categories
def collect_elements_from_selected_categories(selected_categories):
    elements = {}
    for category_name in selected_categories:
        bic = getattr(BuiltInCategory, 'OST_' + category_name.replace(" ", ""))
        category_filter = ElementCategoryFilter(bic)
        collector = FilteredElementCollector(doc).WherePasses(category_filter).WhereElementIsNotElementType().ToElements()
        elements[category_name] = list(collector)
    return elements

# Function to pair elements (generalized for any two categories)
def get_paired_elements(elements, selected_categories):
    paired_elements = []
    if len(selected_categories) == 2:
        cat1, cat2 = selected_categories
        for elem1 in elements[cat1]:
            for elem2 in elements[cat2]:
                paired_elements.append((elem1, elem2))
    return paired_elements

# Main script execution
all_model_categories = get_model_categories_in_use(doc)
selected_categories = forms.SelectFromList.show(all_model_categories,
                                                multiselect=True,
                                                button_name='Select Categories')

if selected_categories and len(selected_categories) == 2:
    elements = collect_elements_from_selected_categories(selected_categories)
    paired_elements = get_paired_elements(elements, selected_categories)
    if paired_elements:
        join_unjoin_choice = forms.CommandSwitchWindow.show(['Join', 'Unjoin'], message='Choose an action:')
        if join_unjoin_choice == 'Join':
            join_elements(paired_elements)
        elif join_unjoin_choice == 'Unjoin':
            unjoin_elements(paired_elements)
