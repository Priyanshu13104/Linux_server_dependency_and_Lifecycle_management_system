from modules.service_monitor import get_service_status
from utils.command_executor import execute
from utils.validators import validate_service_name


DEPENDENCY_PROPERTIES = {
    "Requires": "requirement",
    "Wants": "optional",
    "Requisite": "requirement",
    "BindsTo": "lifecycle",
    "PartOf": "lifecycle",
}


def get_unit_dependencies(service_name):
    if not validate_service_name(service_name):
        return []
    result = execute([
        "systemctl", "show", service_name, "--no-pager",
        "-p", "Requires", "-p", "Wants", "-p", "Requisite",
        "-p", "BindsTo", "-p", "PartOf", "-p", "After", "-p", "Before",
    ])
    if not result["success"]:
        return []
    relationships = []
    for line in result["stdout"].splitlines():
        if "=" not in line:
            continue
        property_name, value = line.split("=", 1)
        if property_name in ("After", "Before"):
            relationship_type = "ordering"
        else:
            relationship_type = DEPENDENCY_PROPERTIES.get(property_name, "relationship")
        for dependency in value.split():
            if dependency:
                relationships.append({
                    "property": property_name,
                    "type": relationship_type,
                    "dependency": dependency,
                })
    return relationships


def get_reverse_dependencies(service_name):
    if not validate_service_name(service_name):
        return []
    result = execute([
        "systemctl", "show", "--no-pager", "--property=RequiredBy",
        "--property=WantedBy", "--property=BoundBy", "--property=PartOf",
        service_name,
    ])
    if not result["success"]:
        return []
    reverse = []
    for line in result["stdout"].splitlines():
        if "=" not in line:
            continue
        property_name, value = line.split("=", 1)
        for unit in value.split():
            reverse.append({
                "property": property_name,
                "dependency": unit,
            })
    return reverse


def dependency_status(service_name):
    health = []
    for relationship in get_unit_dependencies(service_name):
        dependency = relationship["dependency"]
        status = get_service_status(dependency)
        health.append({
            **relationship,
            "status": status.get("active", "unknown"),
            "load": status.get("load", "unknown"),
            "healthy": (
                relationship["type"] != "requirement"
                or status.get("active") == "active"
            ) if status.get("success") else False,
        })
    return health


def dependency_tree(service_name, max_depth=4, visited=None, depth=0):
    if visited is None:
        visited = set()
    if depth > max_depth or service_name in visited:
        return {"name": service_name, "cycle": service_name in visited, "children": []}
    visited.add(service_name)
    children = []
    for relationship in get_unit_dependencies(service_name):
        dependency = relationship["dependency"]
        child = dependency_tree(dependency, max_depth, visited, depth + 1)
        child["relationship"] = relationship
        children.append(child)
    return {"name": service_name, "cycle": False, "children": children}


def unhealthy_dependencies(service_name):
    return [
        item for item in dependency_status(service_name)
        if not item["healthy"] and item["type"] in ("requirement", "lifecycle")
    ]
