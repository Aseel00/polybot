from pathlib import Path
from matplotlib.image import imread, imsave
import random

def rgb2gray(rgb):
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray


class Img:

    def __init__(self, path):
        """
        Do not change the constructor implementation
        """
        self.path = Path(path)
        self.data = rgb2gray(imread(path)).tolist()

    def save_img(self):
        """
        Do not change the below implementation
        """
        new_path = self.path.with_name(self.path.stem + '_filtered' + self.path.suffix)
        imsave(new_path, self.data, cmap='gray')
        return new_path

    def blur(self, blur_level=16):

        height = len(self.data)
        width = len(self.data[0])
        filter_sum = blur_level ** 2

        result = []
        for i in range(height - blur_level + 1):
            row_result = []
            for j in range(width - blur_level + 1):
                sub_matrix = [row[j:j + blur_level] for row in self.data[i:i + blur_level]]
                average = sum(sum(sub_row) for sub_row in sub_matrix) // filter_sum
                row_result.append(average)
            result.append(row_result)

        self.data = result

    def contour(self):
        for i, row in enumerate(self.data):
            res = []
            for j in range(1, len(row)):
                res.append(abs(row[j-1] - row[j]))

            self.data[i] = res

    def rotate(self):
        # TODO remove the `raise` below, and write your implementation
        height = len(self.data)
        width = len(self.data[0])

        rotated = []
        for j in range(width):
            new_row = []
            for i in range(height - 1, -1, -1):
                new_row.append(self.data[i][j])

            rotated.append(new_row)
        self.data = rotated

    def salt_n_pepper(self):
        # TODO remove the `raise` below, and write your implementation
        for i in range(0,len(self.data)):
            for j in range(0,len(self.data[0])):
                random_val=random.random()
                if random_val < 0.2:
                    self.data[i][j]=255
                elif random_val > 0.8:
                    self.data[i][j]=0

    def concat(self, other_img, direction='horizontal'):
        # TODO remove the `raise` below, and write your implementation
        result = []
        if not isinstance(other_img, Img):
            raise RuntimeError("Input must be an instance of Tmg class.")
        if direction == 'horizontal':
            if len(self.data) != len(other_img.data):
                raise RuntimeError("Images must have the same height for horizontal concatenation")
            result = [row1 + row2 for row1, row2 in zip(self.data, other_img.data)]

        elif direction == 'vertical':
            if len(self.data[0]) != len(other_img.data[0]):
                raise RuntimeError("Images must have the same width for vertical concatenation")
            result = self.data + other_img.data
        else:
            raise RuntimeError("Unsupported direction")
        self.data = result

    def segment(self):
        # TODO remove the `raise` below, and write your implementation
        for i in range(0,len(self.data)):
            for j in range(0,len(self.data[0])):
                if self.data[i][j] > 100:
                    self.data[i][j]=255
                else:
                    self.data[i][j]=0
