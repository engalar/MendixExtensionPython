# Mendix Untyped API - DomainModel DSL Generator Guide

## Overview

This document describes the untyped API patterns used in the `DomainModelAnalyzer` class for generating DSL documentation from Mendix domain models.

## Core Concepts

### Typed vs Untyped API

**Typed API** (Old - deprecated for module access):
```python
# Direct property access
domain_model = module.DomainModel
entities = domain_model.GetEntities()
entity.Name
entity.Documentation
```

**Untyped API** (New - required):
```python
# String-based property access
dm_units = module.GetUnitsOfType("DomainModels$DomainModel")
domain_model = next((dm for dm in dm_units), None)
entities_prop = domain_model.GetProperty("entities")
entities = list(entities_prop.GetValues())
entity.GetProperty("name").Value
entity.GetProperty("documentation").Value
```

## Type Naming Convention

All Mendix types use the format: `Module$TypeName`

Common types:
- `Projects$Module`
- `DomainModels$DomainModel`
- `DomainModels$Entity`
- `DomainModels$Attribute`
- `DomainModels$Association`
- `DomainModels$CrossAssociation`

## Core API Methods

### 1. Finding Units

```python
# Get all units of a specific type from a container
modules = root.GetUnitsOfType("Projects$Module")
domain_models = module.GetUnitsOfType("DomainModels$DomainModel")
```

### 2. Accessing Properties

```python
# Get a property object
prop = obj.GetProperty("propertyName")

# Check if property exists
if prop:
    value = prop.Value

# Check if property is a list
if prop and prop.IsList:
    items = list(prop.GetValues())
```

### 3. Accessing Object Metadata

```python
# Get type name
type_name = obj.Type  # Returns "DomainModels$Entity"

# Get object ID
id = obj.ID.ToString()

# Get object name
name = obj.Name
```

## Common Patterns

### Pattern 1: Finding and Processing Domain Models

```python
# Find domain model in module
dm_units = module.GetUnitsOfType("DomainModels$DomainModel")
domain_model = next((dm for dm in dm_units), None)

if not domain_model:
    return "Error: No domain model found"
```

### Pattern 2: Processing List Properties

```python
# Always check IsList before GetValues()
entities_prop = domain_model.GetProperty("entities")
if entities_prop and entities_prop.IsList:
    entities = list(entities_prop.GetValues())
    for entity in entities:
        # Process each entity
        name = entity.GetProperty("name").Value
```

### Pattern 3: Safe Property Access

```python
# Get property with null checks
name_prop = entity.GetProperty("name")
name = name_prop.Value if name_prop else "Unknown"

# Nested property access
doc_prop = entity.GetProperty("documentation")
doc = doc_prop.Value if doc_prop and doc_prop.Value else ""
```

### Pattern 4: Building ID Maps

```python
# Build ID to name mapping for resolving references
id_map = {}
for ent in entities:
    id_map[ent.ID.ToString()] = f"{module.Name}.{ent.Name}"

# Use in association lookups
parent_name = id_map.get(parent_id, "Unknown")
```

## Attribute Type Detection

Attributes have different types that need to be detected by the type string:

```python
def get_attribute_type_string(attr):
    type_prop = attr.GetProperty("type")
    attr_type = type_prop.Value
    type_name = attr_type.Type  # e.g., "DomainModels$StringAttributeType"

    if "StringAttributeType" in type_name:
        length_prop = attr_type.GetProperty("length")
        length = length_prop.Value if length_prop and length_prop.Value is not None else 0
        return f"String({length if length > 0 else 'Unlimited'})"
    elif "IntegerAttributeType" in type_name:
        return "Integer"
    # ... etc
```

## Common Attribute Types

| Type Name | Display Name | Special Handling |
|-----------|-------------|------------------|
| StringAttributeType | String(length) | Length property may be None |
| IntegerAttributeType | Integer | - |
| LongAttributeType | Long | - |
| DecimalAttributeType | Decimal | - |
| BooleanAttributeType | Boolean | - |
| DateTimeAttributeType | DateTime | - |
| AutoNumberAttributeType | AutoNumber | - |
| EnumerationAttributeType | Enum(name) | Get enumeration name |
| BinaryAttributeType | Binary | - |
| HashedStringAttributeType | HashString | - |

## Association Handling

### Internal Associations

```python
associations_prop = domain_model.GetProperty("associations")
if associations_prop and associations_prop.IsList:
    associations = list(associations_prop.GetValues())
    for assoc in associations:
        # Get parent/child entities
        parent_prop = assoc.GetProperty("parent")
        child_prop = assoc.GetProperty("child")
        parent_id = str(parent_prop.Value.ID) if parent_prop and parent_prop.Value else "Unknown"
        child_id = str(child_prop.Value.ID) if child_prop and child_prop.Value else "Unknown"
```

### Cross-Module Associations

```python
cross_assocs_prop = domain_model.GetProperty("crossAssociations")
if cross_assocs_prop and cross_assocs_prop.IsList:
    cross_associations = list(cross_assocs_prop.GetValues())
    for assoc in cross_associations:
        # Child might be a qualified name string
        child_prop = assoc.GetProperty("child")
        child_name = str(child_prop.Value) if child_prop and child_prop.Value else "Unknown"
```

## Generalization Handling

```python
# Check entity persistability
gen_prop = entity.GetProperty("generalization")
if gen_prop and gen_prop.Value:
    gen = gen_prop.Value

    # Check for parent entity (IGeneralization)
    parent_qname_prop = gen.GetProperty("generalization")
    if parent_qname_prop and parent_qname_prop.Value:
        # Has parent
        return f" extends {parent_qname_prop.Value}"

    # Check persistable flag (INoGeneralization)
    persistable_prop = gen.GetProperty("persistable")
    if persistable_prop and persistable_prop.Value is not None:
        return persistable_prop.Value
```

## Error Handling Best Practices

### 1. Always Check Property Existence

```python
# Wrong - will throw exception
name = entity.GetProperty("name").Value

# Correct - safe access
name_prop = entity.GetProperty("name")
name = name_prop.Value if name_prop else "Unknown"
```

### 2. Handle None Values

```python
# Wrong - None doesn't convert to int
length = int(length_prop.Value) if length_prop else 0

# Correct - explicit None check
length = length_prop.Value if length_prop and length_prop.Value is not None else 0
```

### 3. Use Exception Handling

```python
try:
    # Complex property access
    type_prop = attr.GetProperty("type")
    attr_type = type_prop.Value
    # ... more processing
except Exception:
    return "Unknown"
```

## Performance Considerations

### 1. Build Lookup Tables

```python
# Build ID map once for O(1) lookups
id_map = {ent.ID.ToString(): ent.Name for ent in entities}

# Instead of searching repeatedly
parent_name = id_map.get(parent_id, "Unknown")
```

### 2. Use list() Carefully

```python
# GetValues() returns an iterator - convert only if needed
if entities_prop and entities_prop.IsList:
    entities = list(entities_prop.GetValues())
```

## Testing Checklist

When testing domain model DSL generation:

- [ ] Module with no domain model returns error message
- [ ] Module with empty domain model shows "No entities found"
- [ ] Entity names, attributes, and types display correctly
- [ ] Documentation appears when include_documentation=True
- [ ] Location appears when include_location=True
- [ ] Internal associations show entity names correctly
- [ ] Cross-module associations show qualified names
- [ ] Generalization info shows "extends ParentEntity"
- [ ] Persistable flag shows [Persistable] or [Non-Persistable]
- [ ] String attributes show length correctly
- [ ] Enumeration attributes show enum name
- [ ] All edge cases handled (None values, missing properties)

## Related Documentation

- [API_CONSTRAINTS.md](./API_CONSTRAINTS.md) - Complete untyped API constraints
- [MENDIX_FRAMEWORK.md](./MENDIX_FRAMEWORK.md) - Framework design and patterns
- [debug2.py](../../debug2.py) - Reference implementation

## Migration Guide

### Converting Typed API to Untyped API

**Before (Typed):**
```python
domain_model = module.DomainModel
entities = list(domain_model.GetEntities())
for entity in entities:
    name = entity.Name
    attrs = list(entity.GetAttributes())
```

**After (Untyped):**
```python
dm_units = module.GetUnitsOfType("DomainModels$DomainModel")
domain_model = next((dm for dm in dm_units), None)
entities_prop = domain_model.GetProperty("entities")
entities = list(entities_prop.GetValues()) if entities_prop and entities_prop.IsList else []
for entity in entities:
    name_prop = entity.GetProperty("name")
    name = name_prop.Value if name_prop else "Unknown"
    attrs_prop = entity.GetProperty("attributes")
    attrs = list(attrs_prop.GetValues()) if attrs_prop and attrs_prop.IsList else []
```
