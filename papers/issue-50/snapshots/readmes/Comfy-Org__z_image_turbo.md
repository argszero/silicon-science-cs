---
license: apache-2.0
tags:
- comfyui
- diffusion-single-file
base_model:
- Tongyi-MAI/Z-Image-Turbo
---

# Z-Image Turbo

Repackaged model files for ComfyUI.

Original model repository: https://huggingface.co/Tongyi-MAI/Z-Image-Turbo

Place the files in the following folders:

```
📂 ComfyUI/
├── 📂 models/
│   ├── 📂 diffusion_models/
│   │   ├── z_image_turbo_bf16.safetensors
│   │   ├── z_image_turbo_int8_convrot.safetensors
│   │   └── z_image_turbo_nvfp4.safetensors
│   ├── 📂 loras/
│   │   └── z_image_turbo_distill_patch_lora_bf16.safetensors
│   ├── 📂 text_encoders/
│   │   ├── qwen_3_4b.safetensors
│   │   ├── qwen_3_4b_fp4_mixed.safetensors
│   │   └── qwen_3_4b_fp8_mixed.safetensors
│   └── 📂 vae/
│       └── ae.safetensors
```

Workflows: https://comfyanonymous.github.io/ComfyUI_examples/z_image/
