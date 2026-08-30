---
license: creativeml-openrail-m
language:
- en
tags:
- comfyui
- diffusion-single-file
base_model:
- runwayml/stable-diffusion-v1-5
---

# Stable Diffusion v1.5 Archive

Repackaged model files for ComfyUI.

Original model repository: https://huggingface.co/runwayml/stable-diffusion-v1-5

Place the files in the following folders:

```
📂 ComfyUI/
├── 📂 models/
│   ├── 📂 checkpoints/
│   │   ├── interiordesignsuperm_v2.safetensors
│   │   ├── v1-5-pruned-emaonly-fp16.safetensors
│   │   └── v1-5-pruned-emaonly.safetensors
```

---

## Stable Diffusion v1.5

This is an archival re-upload of Stable Diffusion v1.5, originally at https://huggingface.co/runwayml/stable-diffusion-v1-5 until RunwayML took down that page.

This model is from 2022, and is several major generational upgrades behind, it is being preserved here for technical & accessibility reasons (eg legacy model testing).

https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/blob/main/v1-5-pruned-emaonly.safetensors is the exact original hash-identical model as uploaded by RunwayML.

https://huggingface.co/Comfy-Org/stable-diffusion-v1-5-archive/blob/main/v1-5-pruned-emaonly-fp16.safetensors is that model converted to FP16, with a metadata header added.
