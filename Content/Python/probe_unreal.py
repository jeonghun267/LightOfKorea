"""Inspect the installed editor API without changing assets."""
import json
import traceback
from pathlib import Path
import unreal

def main():
    try:
        names = ["EditorLevelLibrary", "LevelEditorSubsystem", "EditorActorSubsystem",
                 "MaterialEditingLibrary", "MaterialExpressionNoise", "MaterialExpressionVectorNoise",
                 "MaterialExpressionCustom", "MaterialExpressionCollectionParameter",
                 "MaterialParameterCollection", "CollectionScalarParameter", "CollectionVectorParameter",
                 "SubobjectDataSubsystem", "SubobjectDataBlueprintFunctionLibrary", "AddNewSubobjectParams",
                 "BlueprintEditorLibrary", "NiagaraSystemFactoryNew", "NiagaraSystem",
                 "MovieSceneMaterialParameterCollectionTrack", "MovieSceneParameterSection",
                 "MovieSceneScriptingDoubleChannel", "MovieSceneNiagaraSystemTrack",
                 "MovieSceneNiagaraSystemSpawnSection", "MovieSceneSequenceExtensions",
                 "EditorLoadingAndSavingUtils", "AutomationLibrary", "EditorLevelUtils",
                 "LevelSequenceActor", "MovieSceneFloatTrack", "MovieSceneCameraCutSection",
                 "MovieSceneObjectBindingID", "NiagaraComponent", "CustomInput",
                 "NiagaraEmitter", "NiagaraEmitterHandle", "NiagaraSystemConversionContext",
                 "NiagaraConversionResults", "FXConverterUtilitiesLibrary", "NiagaraEmitterConversionContext",
                 "PostProcessSettings", "LevelSequencePlaybackSettings", "MaterialExpressionTransformPosition",
                 "FXConverterUtilitiesLibrary", "NiagaraSystemConversionContext", "NiagaraEmitterConversionContext",
                 "NiagaraScriptConversionContext", "CreateScriptContextArgs", "NiagaraSpriteRendererProperties"]
        report = {}
        for name in names:
            cls = getattr(unreal, name, None)
            report[name] = {"doc": getattr(cls, "__doc__", ""),
                            "members": [x for x in dir(cls) if not x.startswith("_")] if cls else []}
        methods = {"SubobjectDataSubsystem": ["add_new_subobject", "rename_subobject", "attach_subobject"],
                   "SubobjectDataBlueprintFunctionLibrary": ["get_data", "get_object", "get_object_for_blueprint"],
                   "MovieSceneParameterSection": ["add_scalar_parameter_key"],
                   "MovieSceneScriptingDoubleChannel": ["add_key"],
                   "EditorLevelUtils": ["add_level_to_world"],
                   "EditorLevelLibrary": ["new_level", "save_current_level"],
                   "MovieSceneSequenceExtensions": ["make_binding_id"],
                   "BlueprintEditorLibrary": ["create_blueprint_asset_with_parent", "add_member_variable"],
                   "NiagaraComponent": ["set_variable_float", "set_system_fixed_bounds"],
                   "AutomationLibrary": ["take_high_res_screenshot"]}
        for name, members in methods.items():
            report[name]["method_docs"] = {m: getattr(getattr(getattr(unreal, name, None), m, None), "__doc__", "") for m in members}
        report["NiagaraNames"] = [n for n in dir(unreal) if "Niagara" in n or "FXConverter" in n]
        for name in ["FXConverterUtilitiesLibrary", "NiagaraSystemConversionContext", "NiagaraEmitterConversionContext", "NiagaraScriptConversionContext"]:
            cls = getattr(unreal,name,None)
            report[name]["method_docs"] = {m:getattr(getattr(cls,m,None),"__doc__","") for m in report[name]["members"] if not m.startswith("get_") or m in ["get_all_renderers","get_emitter"]}
        out = Path(unreal.Paths.project_saved_dir()) / "LOK" / "api_probe.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        unreal.log("[LOK][INFO] API probe complete: " + str(out))
    except Exception:
        unreal.log_error("[LOK][ERROR] " + traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
