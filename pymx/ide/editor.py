import traceback
from Mendix.StudioPro.ExtensionsAPI.Model.Microflows import IMicroflow  # type: ignore
import importlib
# import module to use
from pymx.model import module as _module

# https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.UI.Services/IDockingWindowService/TryOpenEditor.md
# https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.UI.Services/IDockingWindowService/TryGetActiveEditor.md


def open_document(ctx, qualifiedName, elementName):
    importlib.reload(_module)
    reports = []
    elementName = None  # TODO: implement later
    # resolve document by qualifiedName
    # due to i don't know the document type, i use loop module document to resolve it
    try:
        abstractUnit, _reports = _module.getAbstractUnitByQualifiedName(
            ctx, qualifiedName)
        if _reports:
            reports.extend(_reports)
        if abstractUnit is None:
            reports.append(
                f"Could not resolve document with qualified name: {qualifiedName}")
            return False, reports
        reports.append(
            f"Successfully resolved document with qualified name: {qualifiedName}")
    except Exception as e:
        reports.append(
            f"Error resolving document with qualified name {qualifiedName}: {str(e)}")
        reports.append(traceback.format_exc())
        return False, reports

    # https://github.com/mendix/ExtensionAPI-Samples/blob/main/API%20Reference/Mendix.StudioPro.ExtensionsAPI.Services/IMicroflowService/GetAllMicroflowActivities.md

    # if qualifiedName is microflow, find elementName
    try:
        # ctx.CurrentApp.ToQualifiedName[IMicroflow](qualifiedName).Resolve()
        mf = None
        if mf:
            reports.append(
                f"Document identified as microflow: {qualifiedName}")
            activities = ctx.microflowService.GetAllMicroflowActivities(mf)
            reports.append(f"Found {len(activities)} activities in microflow")
            activity_found = False
            for activity in activities:
                if activity.Name == elementName:
                    success = ctx.dockingWindowService.TryOpenEditor(
                        mf, activity)
                    if success:
                        reports.append(
                            f"Successfully opened microflow: {qualifiedName} and focused activity: {elementName}")
                    else:
                        reports.append(
                            f"Failed to open microflow: {qualifiedName} and focused activity: {elementName}")
                    activity_found = True
                    break

            if not activity_found:
                reports.append(
                    f"Activity with name '{elementName}' not found in microflow '{qualifiedName}'")
                return False, reports
        else:
            success = ctx.dockingWindowService.TryOpenEditor(
                abstractUnit, None)
            if success:
                reports.append(
                    f"Successfully opened document: {qualifiedName}")
            else:
                reports.append(f"Failed to open document: {qualifiedName}")
    except Exception as e:
        reports.append(
            f"Error opening document {qualifiedName} with element {elementName}: {str(e)}")
        return False, reports

    return success, reports
