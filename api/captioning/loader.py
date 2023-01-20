from torchvision import transforms
from torch.utils.data import Dataset
from torchvision.transforms.functional import InterpolationMode
from torch.utils.data import DataLoader


class ImagesDataset(Dataset):
    def __init__(self, imgs_dict, configs):
        image_size = configs["dataset"]["image_size"]
        self.transform = transforms.Compose(
            [
                transforms.Resize(
                    (image_size, image_size), interpolation=InterpolationMode.BICUBIC
                ),
                transforms.ToTensor(),
                transforms.Normalize(
                    (0.48145466, 0.4578275, 0.40821073),
                    (0.26862954, 0.26130258, 0.27577711),
                ),
            ]
        )
        self.filenames = []
        self.imgs_list = []
        for filename, img in imgs_dict.items():
            self.filenames.append(filename)
            self.imgs_list.append(img)

    def __len__(self):
        return len(self.filenames)

    def __getitem__(self, index):
        filename = self.filenames[index]
        image = self.imgs_list[index]
        image = self.transform(image)

        return image, filename


def create_loader(imgs_dict, configs):
    # create dataset
    dataset = ImagesDataset(imgs_dict, configs)
    loader = DataLoader(
        dataset,
        batch_size=configs["dataset"]["batch_size"],
        num_workers=configs["dataset"]["num_workers"],
    )
    return loader
