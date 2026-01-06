// Decompiled with JetBrains decompiler
// Type: Mendix.StudioPro.ExtensionsAPI.Services.IMicroflowActivitiesService
// Assembly: Mendix.StudioPro.ExtensionsAPI, Version=10.24.13.0, Culture=neutral, PublicKeyToken=null
// MVID: ADDE99EE-DA47-4D6D-9B00-D2E608B2DFB4
// Assembly location: D:\Program Files\Mendix\10.24.13.86719\modeler\Mendix.StudioPro.ExtensionsAPI.dll
// XML documentation location: D:\Program Files\Mendix\10.24.13.86719\modeler\Mendix.StudioPro.ExtensionsAPI.xml

using Mendix.StudioPro.ExtensionsAPI.Model;
using Mendix.StudioPro.ExtensionsAPI.Model.DataTypes;
using Mendix.StudioPro.ExtensionsAPI.Model.DomainModels;
using Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions;
using Mendix.StudioPro.ExtensionsAPI.Model.Microflows;
using Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions;

#nullable enable
namespace Mendix.StudioPro.ExtensionsAPI.Services;

/// <summary>
/// Provides a series of operations for creating various types of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> for a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IMicroflow" />.
/// </summary>
public interface IMicroflowActivitiesService
{
  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.ICreateObjectAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="entity">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> of the new object.</param>
  /// <param name="outputVariableName">The name of the new object created by the activity.</param>
  /// <param name="commit">It determines if and how the activity should commit the new object to the database.</param>
  /// <param name="refreshInClient">This defines how changes are reflected in the pages presented to the end-user.</param>
  /// <param name="initialValues">Optional initial set of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> for the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" />.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.ICreateObjectAction" />.</returns>
  IActionActivity CreateCreateObjectActivity(
    IModel model,
    IEntity entity,
    string outputVariableName,
    CommitEnum commit,
    bool refreshInClient,
    params (string attribute, IMicroflowExpression valueExpression)[] initialValues);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IChangeObjectAction" />.
  /// It will use a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> to change the value of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> provided.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="attribute">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> to change with the expression.</param>
  /// <param name="changeType">The type of change. Could be <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions.ChangeActionItemType.Set" />, <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions.ChangeActionItemType.Add" /> or <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions.ChangeActionItemType.Remove" />.</param>
  /// <param name="newValueExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> used to change the value of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" />.</param>
  /// <param name="changeVariableName">The name of the existing variable in scope to change with this activity.</param>
  /// <param name="commit">It determines if and how the activity should commit the changes to the database.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IChangeObjectAction" />.</returns>
  IActionActivity CreateChangeAttributeActivity(
    IModel model,
    IAttribute attribute,
    ChangeActionItemType changeType,
    IMicroflowExpression newValueExpression,
    string changeVariableName,
    CommitEnum commit);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IChangeObjectAction" />.
  /// It will use a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> to change the value of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" /> provided.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="association">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" /> to change with the expression.</param>
  /// <param name="changeType">The type of change. Could be <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions.ChangeActionItemType.Set" />, <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions.ChangeActionItemType.Add" /> or <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions.ChangeActionItemType.Remove" />.</param>
  /// <param name="newValueExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> used to change the value of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</param>
  /// <param name="changeVariableName">The name of the existing variable in scope to change with this activity.</param>
  /// <param name="commit">It determines if and how the activity should commit the changes to the database.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IChangeObjectAction" />.</returns>
  IActionActivity CreateChangeAssociationActivity(
    IModel model,
    IAssociation association,
    ChangeActionItemType changeType,
    IMicroflowExpression newValueExpression,
    string changeVariableName,
    CommitEnum commit);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.ICommitAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="commitVariableName">The name of the existing variable in scope to commit with this activity.</param>
  /// <param name="withEvents"></param>
  /// <param name="refreshInClient">This defines how changes are reflected in the pages presented to the end-user.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.ICommitAction" />.</returns>
  IActionActivity CreateCommitObjectActivity(
    IModel model,
    string commitVariableName,
    bool withEvents = true,
    bool refreshInClient = false);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IRollbackAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="rollbackVariableName">The name of the existing variable in scope to rollback with this activity.</param>
  /// <param name="refreshInClient">This defines how changes are reflected in the pages presented to the end-user.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IRollbackAction" />.</returns>
  IActionActivity CreateRollbackObjectActivity(
    IModel model,
    string rollbackVariableName,
    bool refreshInClient = false);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IDeleteAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="deleteVariableName">The name of the existing variable in scope to delete with this activity.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IDeleteAction" />.</returns>
  IActionActivity CreateDeleteObjectActivity(IModel model, string deleteVariableName);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IRetrieveAction" />. This method is used to create
  /// the retrieve action which will only retrieve items from the database. It will also add a range of values for the retrieval of data from the database.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="outputVariableName">The name of the object retrieved from the database. It could be a single item or a list.</param>
  /// <param name="entity">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" />to query the database for.</param>
  /// <param name="xPathConstraint">The condition the objects need to fulfill to be retrieved. If not supplied, all objects of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> are retrieved.</param>
  /// <param name="range">One <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" />for the starting index and one for the amount of items to retrieve.</param>
  /// <param name="attributesToSortBy">A set of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> to sort by. They can individually be either ascending or descending.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IRetrieveAction" /> for database retrieval with a custom range.</returns>
  IActionActivity CreateDatabaseRetrieveSourceActivity(
    IModel model,
    string outputVariableName,
    IEntity entity,
    string? xPathConstraint,
    (IMicroflowExpression startingIndex, IMicroflowExpression amount) range,
    params AttributeSorting[] attributesToSortBy);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IRetrieveAction" />. This method is used to create
  /// the retrieve action which will only retrieve items from the database. It can be specified if it should retrieve all items or just the first item from the database.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="outputVariableName">The name of the object retrieved from the database. It could be a single item or a list.</param>
  /// <param name="entity">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" />to query the database for.</param>
  /// <param name="xPathConstraint">The condition the objects need to fulfill to be retrieved. If not supplied, all objects of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> are retrieved.</param>
  /// <param name="retrieveJustFirstItem">If true, only the first item matching is returned. If false, all items are returned.</param>
  /// <param name="attributesToSortBy">A set of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> to sort by. They can individually be either ascending or descending.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IRetrieveAction" /> for database retrieval.</returns>
  IActionActivity CreateDatabaseRetrieveSourceActivity(
    IModel model,
    string outputVariableName,
    IEntity entity,
    string? xPathConstraint,
    bool retrieveJustFirstItem,
    params AttributeSorting[] attributesToSortBy);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IRetrieveAction" />. This method is used to create
  /// the retrieve action which will only retrieve items by an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="association">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />used to retrieve items.</param>
  /// <param name="outputVariableName">The name of the object retrieved. It will be a list.</param>
  /// <param name="entityVariableName">The entity variable in scope for the association.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IRetrieveAction" /> for retrieval of items by an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</returns>
  IActionActivity CreateAssociationRetrieveSourceActivity(
    IModel model,
    IAssociation association,
    string outputVariableName,
    string entityVariableName);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.ICreateListAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="entity">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IEntity" /> to create a list of.</param>
  /// <param name="outputVariableName">The name of the new list variable.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.ICreateListAction" />.</returns>
  IActionActivity CreateCreateListActivity(IModel model, IEntity entity, string outputVariableName);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IChangeListAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="operation">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions.ChangeListActionOperation" /> which determines the type of change.</param>
  /// <param name="listVariableName">The name of the list variable in scope to change.</param>
  /// <param name="changeValueExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> to apply the change to the list.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IChangeListAction" />.</returns>
  IActionActivity CreateChangeListActivity(
    IModel model,
    ChangeListActionOperation operation,
    string listVariableName,
    IMicroflowExpression changeValueExpression);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.ISort" /> action.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="listVariableName">The name of the list variable in scope to sort.</param>
  /// <param name="outputVariableName">The name of the new sorted list.</param>
  /// <param name="attributesToSortBy">A set of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> to sort by. They can individually be either ascending or descending.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.ISort" /> action.</returns>
  IActionActivity CreateSortListActivity(
    IModel model,
    string listVariableName,
    string outputVariableName,
    params AttributeSorting[] attributesToSortBy);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFilter" /> action.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="association">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" /> to filter by.</param>
  /// <param name="listVariableName">The name of the list variable in scope to filter.</param>
  /// <param name="outputVariableName">The name of the new filtered list.</param>
  /// <param name="filterExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> which performs the filtering.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFilter" /> action by <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</returns>
  IActionActivity CreateFilterListByAssociationActivity(
    IModel model,
    IAssociation association,
    string listVariableName,
    string outputVariableName,
    IMicroflowExpression filterExpression);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFilter" /> action.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="attribute">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> to filter by.</param>
  /// <param name="listVariableName">The name of the list variable in scope to filter.</param>
  /// <param name="outputVariableName">The name of the new filtered list.</param>
  /// <param name="filterExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> which performs the filtering.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFilter" /> action by <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" />.</returns>
  IActionActivity CreateFilterListByAttributeActivity(
    IModel model,
    IAttribute attribute,
    string listVariableName,
    string outputVariableName,
    IMicroflowExpression filterExpression);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFindByExpression" /> action.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="listVariableName">The name of the list variable in scope to search.</param>
  /// <param name="outputVariableName">The name of the search result object.</param>
  /// <param name="findExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> used to perform the search.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFindByExpression" /> action.</returns>
  IActionActivity CreateFindByExpressionActivity(
    IModel model,
    string listVariableName,
    string outputVariableName,
    IMicroflowExpression findExpression);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFind" /> action.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="attribute">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> used to perform the search.</param>
  /// <param name="listVariableName">The name of the list variable in scope to search.</param>
  /// <param name="outputVariableName">The name of the search result object.</param>
  /// <param name="findExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> used to compare to the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" />.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFind" /> action.</returns>
  IActionActivity CreateFindByAttributeActivity(
    IModel model,
    IAttribute attribute,
    string listVariableName,
    string outputVariableName,
    IMicroflowExpression findExpression);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFind" /> action.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="association">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" /> used to perform the search.</param>
  /// <param name="listVariableName">The name of the list variable in scope to search.</param>
  /// <param name="outputVariableName">The name of the search result object.</param>
  /// <param name="findExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> used to compare to the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAssociation" />.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IFind" /> action.</returns>
  IActionActivity CreateFindByAssociationActivity(
    IModel model,
    IAssociation association,
    string listVariableName,
    string outputVariableName,
    IMicroflowExpression findExpression);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IListOperation" /> action.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="listVariableName">The list variable in scope to perform the operation on.</param>
  /// <param name="outputVariableName">The new result after the operation is performed.</param>
  /// <param name="listOperation">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IListOperation" /> for the action</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IListOperation" /> action.</returns>
  /// <exception cref="T:System.InvalidOperationException"> when the operation is a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IBinaryListOperation" /> and the 'SecondListOrObjectVariableName' property is not provided.</exception>
  IActionActivity CreateListOperationActivity(
    IModel model,
    string listVariableName,
    string outputVariableName,
    IListOperation listOperation);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IAggregateListAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="inputListVariableName">The list variable in scope which is the input for the aggregate function</param>
  /// <param name="outputVariableName">The new result after the aggregate function is performed</param>
  /// <param name="aggregateFunction">The type of aggregate function.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IAggregateListAction" />.</returns>
  IActionActivity CreateAggregateListActivity(
    IModel model,
    string inputListVariableName,
    string outputVariableName,
    AggregateFunctionEnum aggregateFunction);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IAggregateListAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="expression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> evaluated for each item in the list of objects. Its result is used for the aggregation.</param>
  /// <param name="inputListVariableName">The list variable in scope which is the input for the aggregate function</param>
  /// <param name="outputVariableName">The new result after the aggregate function is performed</param>
  /// <param name="aggregateFunction">The type of aggregate function.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IAggregateListAction" />.</returns>
  IActionActivity CreateAggregateListByExpressionActivity(
    IModel model,
    IMicroflowExpression expression,
    string inputListVariableName,
    string outputVariableName,
    AggregateFunctionEnum aggregateFunction);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IAggregateListAction" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="attribute">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DomainModels.IAttribute" /> of the objects in the list used to aggregate over. This must be a numeric attribute.</param>
  /// <param name="inputListVariableName">The list variable in scope which is the input for the aggregate function</param>
  /// <param name="outputVariableName">The new result after the aggregate function is performed</param>
  /// <param name="aggregateFunction">The type of aggregate function.</param>
  /// <returns>An <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IAggregateListAction" />.</returns>
  IActionActivity CreateAggregateListByAttributeActivity(
    IModel model,
    IAttribute attribute,
    string inputListVariableName,
    string outputVariableName,
    AggregateFunctionEnum aggregateFunction);

  /// <summary>
  /// It creates an <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActionActivity" /> which performs a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IAggregateListAction" /> of type <see cref="F:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.Actions.AggregateFunctionEnum.Reduce" />.
  /// </summary>
  /// <param name="model">The current model of the application.</param>
  /// <param name="inputListVariableName">The list variable in scope which is the input for the aggregate function</param>
  /// <param name="outputVariableName">The new result after the aggregate function is performed</param>
  /// <param name="initialValueExpression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> used for the initial value of the reduce function.</param>
  /// <param name="expression">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> evaluated for each item in the list of objects. Its result is used for the aggregation.</param>
  /// <param name="dataType">The return data type of the reduce operation.</param>
  /// <returns></returns>
  IActionActivity CreateReduceAggregateActivity(
    IModel model,
    string inputListVariableName,
    string outputVariableName,
    IMicroflowExpression initialValueExpression,
    IMicroflowExpression expression,
    DataType dataType);
}
