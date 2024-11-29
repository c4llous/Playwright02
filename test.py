import cv2

# Load the super resolution model
sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel("ESPCN_x4.pb")
sr.setModel("espcn", 4)  # 4x upscaling

# Read image
image = cv2.imread('upscaled_image.jpeg')

# Upscale the image
result = sr.upsample(image)

cv2.imwrite('upscaled_image2.jpeg', result)
