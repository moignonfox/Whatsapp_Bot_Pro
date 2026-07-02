from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

drawing = svg2rlg("vira_icon_violet_ambre.svg")
# Scale it if necessary, but svg2rlg will parse it at the original size
# We can scale it to 1024x1024
from reportlab.graphics.shapes import Drawing
scaling_factor = 1024.0 / max(drawing.width, drawing.height)
drawing.width = drawing.width * scaling_factor
drawing.height = drawing.height * scaling_factor
drawing.scale(scaling_factor, scaling_factor)

renderPM.drawToFile(drawing, "mybot_mobile/assets/icon.png", fmt="PNG")
print("Converted to icon.png")
