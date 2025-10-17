import os
import tifffile
from PIL import Image


def _get_dataset_files(directory_path):
    """
    Helper function to get dataset files from the directory.

    Args:
        directory_path (str): Path to the dataset directory
    Returns: image_files (list), mask_file (str), nuclei_folders (list)
    """
    images_dir = os.path.join(directory_path, "images")
    tracks_dir = os.path.join(directory_path, "tracks")
    nuclei_dir = os.path.join(tracks_dir, "nuclei")

    image_files = sorted(
        [
            os.path.join(images_dir, f)
            for f in os.listdir(images_dir)
            if f.endswith(".tif")
        ]
    )
    mask_file = None
    for f in os.listdir(tracks_dir):
        if f.endswith(".hdf"):
            mask_file = os.path.join(tracks_dir, f)
            break
    nuclei_folders = sorted(
        [
            os.path.join(nuclei_dir, f)
            for f in os.listdir(nuclei_dir)
            if os.path.isdir(os.path.join(nuclei_dir, f))
        ]
    )

    return image_files, mask_file, nuclei_folders


def time_series_data(directory_path, load_images=True, use_pil=False):
    """
    Generator that yields data in time sequence
    Args:
        directory_path (str): Path to the dataset directory
        load_images (bool): Whether to load image data into memory
        use_pil (bool): If True, loads images as PIL.Image, else as numpy arrays

    Yields:
        dict: {
            'image_file': str,       # Path to the image
            'image_data': array/PIL, # Optional, loaded image
            'mask_file': str,        # Path to the mask file
            'nuclei_file': str     # Path to the nuclei file corresponding to this image
        }
    """
    image_files, mask_file, nuclei_files = _get_dataset_files(directory_path)

    # Yield one image at a time
    for idx, image_file in enumerate(image_files):
        image_data = None
        if load_images:
            if use_pil:
                image_data = Image.open(image_file)
            else:
                image_data = tifffile.imread(image_file)

        # Match nuclei folder to image (if number matches)
        nuclei_file = nuclei_files[idx] if idx < len(nuclei_files) else None

        yield {
            "image_file": image_file,
            "image_data": image_data,
            "mask_file": mask_file,
            "nuclei_file": nuclei_file,
        }


def slice_at_a_time(image_files, slice_index, load_images=True, use_pil=False):
    """
    Get data at a specific time index.

    Args:
        image_files (list): List of image file paths
        slice_index (int): Index of the slice to retrieve
        load_images (bool): Whether to load image data into memory
        use_pil (bool): If True, loads images as PIL.Image, else as numpy arrays

    Returns:
        dict: {
            'image_file': str,       # Path to the image
            'slice_index': int,      # Index of the slice
            'slice_data': array/PIL, # Optional, loaded slice data
        }
    """
    for idx, image_file in enumerate(image_files):
        with tifffile.TiffFile(image_file) as tif:
            if slice_index < len(tif.pages):
                slice_data = None
                if load_images:
                    if use_pil:
                        slice_data = Image.fromarray(tif.pages[slice_index].asarray())
                    else:
                        slice_data = tif.pages[slice_index].asarray()

                yield {
                    "image_file": image_file,
                    "slice_index": slice_index,
                    "slice_data": slice_data,
                }
