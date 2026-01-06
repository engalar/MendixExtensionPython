// Decompiled with JetBrains decompiler
// Type: Mendix.StudioPro.ExtensionsAPI.Services.IMicroflowService
// Assembly: Mendix.StudioPro.ExtensionsAPI, Version=10.24.13.0, Culture=neutral, PublicKeyToken=null
// MVID: ADDE99EE-DA47-4D6D-9B00-D2E608B2DFB4
// Assembly location: D:\Program Files\Mendix\10.24.13.86719\modeler\Mendix.StudioPro.ExtensionsAPI.dll
// XML documentation location: D:\Program Files\Mendix\10.24.13.86719\modeler\Mendix.StudioPro.ExtensionsAPI.xml

using Mendix.StudioPro.ExtensionsAPI.Model;
using Mendix.StudioPro.ExtensionsAPI.Model.DataTypes;
using Mendix.StudioPro.ExtensionsAPI.Model.Microflows;
using Mendix.StudioPro.ExtensionsAPI.Model.Projects;
using System;
using System.Collections.Generic;

#nullable enable
namespace Mendix.StudioPro.ExtensionsAPI.Services;

/// <summary>Provides a set of operations on a Microflow.</summary>
public interface IMicroflowService
{
  /// <summary>
  /// Initializes an empty microflow with start and end nodes and the specified <paramref name="parameters" />. It uses ReturnType property of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IMicroflow" /> to set the Return Type./&gt;.
  /// The microflow must be added to the app model first before this method can be used.
  /// </summary>
  /// <param name="microflow">Microflow which is initialized.</param>
  /// <param name="parameters">List of parameters that are set in the microflow.</param>
  /// <exception cref="T:System.InvalidOperationException">Microflow is not added to the app model.</exception>
  void Initialize(IMicroflow microflow, params (string name, DataType type)[] parameters);

  /// <summary>
  /// Creates a microflow and adds it to its containing folder. It initializes it with start and end nodes and the specified <paramref name="parameters" />. It uses ReturnType property of <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IMicroflow" /> to set the Return Type and its value, using the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.MicroflowReturnValue" /> parameter./&gt;.
  /// The microflow must be added to the app model first before this method can be used.
  /// </summary>
  /// <param name="model">The model in which the microflow will be created.</param>
  /// <param name="container">The folder or module in which the microflow will be added.</param>
  /// <param name="name">The name of the microflow.</param>
  /// <param name="returnValue">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.MicroflowReturnValue" /> of the microflow. It has a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.DataTypes.DataType" /> for the return type and a <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.MicroflowExpressions.IMicroflowExpression" /> for the return value. If not passed in, the return value will default to <see cref="P:Mendix.StudioPro.ExtensionsAPI.Model.DataTypes.DataType.Void" /> without a return value.</param>
  /// <param name="parameters">List of parameters that are set in the microflow.</param>
  IMicroflow CreateMicroflow(
    IModel model,
    IFolderBase container,
    string name,
    MicroflowReturnValue? returnValue = null,
    params (string name, DataType type)[] parameters);

  /// <summary>
  /// Inserts <paramref name="activities" /> in the microflow directly after the start event.
  /// </summary>
  /// <param name="microflow">Microflow to which <paramref name="activities" /> are added.</param>
  /// <param name="activities">List of activities to add after the start event.</param>
  bool TryInsertAfterStart(IMicroflow microflow, params IActivity[] activities);

  /// <summary>
  /// Inserts <paramref name="activities" /> in a microflow directly before the <paramref name="insertBeforeActivity" />.
  /// This <paramref name="insertBeforeActivity" /> must be connected in the microflow and must contain exactly 1 incoming <a href="https://docs.mendix.com/refguide/sequence-flow">SequenceFlow</a>.
  /// </summary>
  /// <param name="insertBeforeActivity">The activity in the microflow to act as reference point to insert the <paramref name="activities" />.</param>
  /// <param name="activities">List of activities to add before the <paramref name="insertBeforeActivity" /> activity.</param>
  /// <returns>Returns false if it does not have exactly 1 incoming <a href="https://docs.mendix.com/refguide/sequence-flow">SequenceFlow</a>.</returns>
  bool TryInsertBeforeActivity(IActivity insertBeforeActivity, params IActivity[] activities);

  /// <summary>Get all parameters of a microflow.</summary>
  IReadOnlyList<IMicroflowParameterObject> GetParameters(IMicroflow microflow);

  /// <summary>
  /// Get all activities of a microflow that are exposed as <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IActivity" /> in the API, including nested activities (loop).
  /// Order and nesting of activities cannot be determined from the result.
  /// </summary>
  IReadOnlyList<IActivity> GetAllMicroflowActivities(IMicroflow microflow);

  /// <summary>
  /// When a variable is renamed, this method needs to be called to update all the usages and references to it.
  /// </summary>
  /// <param name="model">The current app known to the extension.</param>
  /// <param name="microflowAction">The <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IMicroflowAction" /> containing the variable to update.</param>
  /// <param name="rename">The actual updating of the name of the variable from the action. The extension has to provide the method. It needs to return the old name and the new name of the variable.</param>
  void UpdateActionAfterRename(
    IModel model,
    IMicroflowAction microflowAction,
    Func<(string oldName, string newName)> rename);

  /// <summary>
  /// It verifies if variable name has already been used in the <see cref="T:Mendix.StudioPro.ExtensionsAPI.Model.Microflows.IMicroflow" />.
  /// </summary>
  /// <param name="microflow">The microflow which contains the variables to check against.</param>
  /// <param name="variableName">The name of the variable used to search for existing variable.</param>
  /// <returns>True if the variable name matches the name of one of the existing variables in the microflow./&gt;</returns>
  bool IsVariableNameInUse(IMicroflow microflow, string variableName);
}
