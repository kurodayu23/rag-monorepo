import numpy as np
import cv2
import torch
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline, UniPCMultistepScheduler
from diffusers.utils import load_image


def generate_controlled_image(prompt: str, reference_image_path: str, out_path: str = "vibe_generated_output.png"):
    """
    ControlNet + Stable Diffusion 示例（偏工程演示用途）。

    你可以把这段代码当成：
    - “把参考图结构（边缘）转成可控条件”
    - 再把它交给 SD 去生成目标画面
    的最小可读示例。

    重要：
    - 需要较高显存（示例里默认推荐 12GB+）
    - 第一次运行可能要下载模型权重
    """

    # 1) 处理参考图：用边缘提取作为 ControlNet 条件
    image = load_image(reference_image_path)
    image = np.array(image)
    low_threshold, high_threshold = 100, 200
    edges = cv2.Canny(image, low_threshold, high_threshold)
    edges = edges[:, :, None]
    canny_image = np.concatenate([edges, edges, edges], axis=2)

    # 2) 加载 ControlNet 与 SD base model
    controlnet = ControlNetModel.from_pretrained(
        "lllyasviel/sd-controlnet-canny",
        torch_dtype=torch.float16,
    )
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        controlnet=controlnet,
        torch_dtype=torch.float16,
    )

    # 3) 调度器与显存优化
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)
    pipe.enable_model_cpu_offload()

    # 4) 生成
    output = pipe(
        prompt,
        image=canny_image,
        num_inference_steps=20,
        guidance_scale=7.5,
    ).images[0]

    output.save(out_path)


if __name__ == "__main__":
    # 示例：不直接执行，避免有人一拉就跑下载/显存开销
    pass

