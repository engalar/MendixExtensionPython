// Decompiled with JetBrains decompiler
// Type: Mendix.StudioPro.ExtensionsAPI.Services.IDomainModelService
// Assembly: Mendix.StudioPro.ExtensionsAPI, Version=10.24.13.0, Culture=neutral, PublicKeyToken=null
// MVID: ADDE99EE-DA47-4D6D-9B00-D2E608B2DFB4
// Assembly location: D:\Program Files\Mendix\10.24.13.86719\modeler\Mendix.StudioPro.ExtensionsAPI.dll
// XML documentation location: D:\Program Files\Mendix\10.24.13.86719\modeler\Mendix.StudioPro.ExtensionsAPI.xml

using Mendix.StudioPro.ExtensionsAPI.Model;
using Mendix.StudioPro.ExtensionsAPI.Model.DomainModels;
using Mendix.StudioPro.ExtensionsAPI.Model.Projects;
using System.Collections.Generic;

#nullable enable
namespace Mendix.StudioPro.ExtensionsAPI.Services;

/// <summary>
/// It provides methods to retrieve associations between entities in the model.
/// </summary>
public interface IDomainModelService
{
  /// <summary>
  /// It returns all <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.EntityAssociation" /> in the current app.
  /// </summary>
  /// <param name="currentApp">The current app.</param>
  /// <param name="modules">The list of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Projects.IModule" /> to search from. If none supplied, all will be searched.</param>
  /// <returns>List of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.EntityAssociation" /></returns>
  IList<EntityAssociation> GetAllAssociations(IModel currentApp, params IModule[] modules);

  /// <summary>
  /// It returns all <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.EntityAssociation" /> in the current app between two <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> objects when one entity is the parent and the other is the child.
  /// </summary>
  /// <param name="currentApp">The current app.</param>
  /// <param name="parent">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> which is the parent of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</param>
  /// <param name="child">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> which is the child of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</param>
  /// <returns>List of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.EntityAssociation" /></returns>
  IList<EntityAssociation> GetAssociationsBetweenEntities(
    IModel currentApp,
    IEntity parent,
    IEntity child);

  /// <summary>
  /// It returns all <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.EntityAssociation" /> in the current app between two <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> objects when both entities supplied are either the parent and the child.
  /// </summary>
  /// <param name="currentApp">The current app.</param>
  /// <param name="entity1">One <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> on one side of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</param>
  /// <param name="entity2">The other <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> on one side of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</param>
  /// <returns>List of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.EntityAssociation" /></returns>
  IList<EntityAssociation> GetAnyAssociationsBetweenEntities(
    IModel currentApp,
    IEntity entity1,
    IEntity entity2);

  /// <summary>
  /// It returns all <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.EntityAssociation" /> in the current app where the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> supplied is the parent or the child, determined by the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.AssociationDirection" />.
  /// </summary>
  /// <param name="currentApp">The current app.</param>
  /// <param name="entity">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> which is either the parent or child (or both) of an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</param>
  /// <param name="associationDirection">The direction of the association to filter by. It can be either <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.AssociationDirection.Parent" />, <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.AssociationDirection.Child" /> or <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.AssociationDirection.Both" />.</param>
  /// <returns></returns>
  IList<EntityAssociation> GetAssociationsOfEntity(
    IModel currentApp,
    IEntity entity,
    AssociationDirection associationDirection);
}
