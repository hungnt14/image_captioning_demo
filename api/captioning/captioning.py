import sys

sys.path.append(".")
import torch


@torch.no_grad()
def generate_captions(model, device, dataloader, configs):
    model.eval()

    results = []
    for image, filenames in dataloader:

        image = image.to(device)

        captions = model.generate(
            image,
            sample=False,
            num_beams=configs["inference"]["num_beams"],
            max_length=configs["inference"]["max_length"],
            min_length=configs["inference"]["min_length"],
            repetition_penalty=1.1,
        )
        for caption, filename in zip(captions, filenames):
            results.append({"filename": filename, "caption": caption})

    return results
