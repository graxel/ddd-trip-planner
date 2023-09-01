
'https://icons8.com'

import base64

folder_path = 'icons/'

avail_dict = {
    'in_range': 'red_d.png',
    'out_of_range': 'grey_d.png',
    'test': 'red_d_clear.png'
}

for category, icon_filename in avail_dict.items():
    with open(folder_path+icon_filename, 'rb') as f:
        file_contents = f.read()
    b64 = base64.b64encode(file_contents).decode('utf-8')
    print(f"    '{category}': "+ '{')
    print(f"        'url': 'data:image/png;base64,{b64}',")
    print(f"        'width': icon_size,")
    print(f"        'height': icon_size,")
    print(f"        'anchorY': icon_size,")
    print( "    },")




