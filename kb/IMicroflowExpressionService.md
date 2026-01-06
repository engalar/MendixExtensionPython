// Decompiled with JetBrains decompiler
// Type: Mendix.StudioPro.ExtensionsAPI.Services.IMicroflowExpressionService
// Assembly: Mendix.StudioPro.ExtensionsAPI, Version=10.24.13.0, Culture=neutral, PublicKeyToken=null
// MVID: ADDE99EE-DA47-4D6D-9B00-D2E608B2DFB4
// Assembly location: D:\Program Files\Mendix\10.24.13.86719\modeler\Mendix.StudioPro.ExtensionsAPI.dll
// XML documentation location: D:\Program Files\Mendix\10.24.13.86719\modeler\Mendix.StudioPro.ExtensionsAPI.xml

using Mendix.StudioPro.ExtensionsAPI.Model;
using Mendix.StudioPro.ExtensionsAPI.Model.DataTypes;
using Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions;

#nullable enable
namespace Mendix.StudioPro.ExtensionsAPI.Services;

/// <summary>
/// Provides a set of operations on a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression">Microflow Expression</see>.
/// </summary>
public interface IMicroflowExpressionService
{
  /// <summary>
  /// Create new <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> from a string <paramref name="value" />.
  /// </summary>
  IMicroflowExpression CreateFromString(string value);

  /// <summary>
  /// Retrieve the type of the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" />, if it has been computed.
  /// </summary>
  /// <param name="model">Reference to the current app.</param>
  /// <param name="microflowExpression">
  /// Microflow expression which type should be determined. It must be a property of an elements that is added to the app model.
  /// </param>
  /// <param name="dataType">
  /// Type of <paramref name="microflowExpression" /> represented by a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DataTypes.DataType" />, or <c>null</c> if it hasn't been computed.
  /// </param>
  /// <returns>
  /// Returns <c>true</c> if data type of the expression is known and <c>false</c> otherwise.
  /// </returns>
  /// <remarks>
  /// Note, that <c>false</c> result can be intermittent and executing <see cref="M:Mendix.StudioPro.ExtensionsAPI.Services.IMicroflowExpressionService.TryGetComputedType(Mendix.StudioPro.ExtensionsAPI.Model.IModel,Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression,Mendix.StudioPro.ExtensionsAPI.Model.DataTypes.DataType@)" /> again at a later point in time might succeed.
  /// </remarks>
  /// <example>
  /// To read the type of an existing expression:
  /// <code>
  /// if (!microflowExpressionOperator.TryGetComputedType(model, modelElement.Property, out var dataType))
  ///     throw new InvalidOperationException();
  /// switch (dataType)
  /// {
  ///     case IStringType:
  ///         return "string";
  ///     case IObjectType objectType:
  ///         return $"object of type {objectType.Entity}";
  ///     // etc
  /// }
  /// </code>
  /// 
  /// This method will never return <c>true</c> when called with an expression that is not part of a model:
  /// <code>
  /// if (microflowExpressionOperator.TryGetComputedType(model, microflowExpressionOperator.CreateFromString(newExpressionValue), out var dataType))
  /// {
  ///     // this code will never execute
  /// }
  /// </code>
  /// 
  /// Nor will it work with an expression that has been just assigned to the app model:
  /// <code>
  /// modelElement.Property = microflowExpressionOperator.CreateFromString(newExpressionValue);;
  /// if (microflowExpressionOperator.TryGetComputedType(model, modelElement.Property, out var dataType))
  /// {
  ///     // this code will never execute
  /// }
  /// </code>
  /// 
  /// If you need to read the type after setting it, use the following approach:
  /// <code>
  /// using var tx = model.StartTransaction("Change argument");
  /// modelElement.Property = microflowExpressionOperator.CreateFromString(newExpressionValue);;
  /// tx.Commit(); // this line is required
  /// 
  /// if (microflowExpressionOperator.TryGetComputedType(model, modelElement.Property, out var dataType))
  /// {
  ///     // use dataType
  /// }
  /// });
  /// </code>
  /// </example>
  bool TryGetComputedType(
    IModel model,
    IMicroflowExpression microflowExpression,
    out DataType? dataType);
}
