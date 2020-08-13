# -*- coding: utf-8 -*-
"""
Description: 
    
    Converts given sprites to b&w images to '.jack' draw functions. 
    They will be encapsulated into the 'SpriteManager.jack' class.
      
    Supported Conversions:
    
    * Sprites_op (+) Pros: converted to optimized sprites (drawn by poking memory)
                 (-) Cons: x-position is a multiple of 16 pixels (one memory adress)

    * Sprites_tp (?) TO-DO

@author: mveselov@mathos.hr
"""

# Parse all sprites into '.jack' files into 'SpriteManager.jack'
def main():
    
    import os
    spriteManagerJack = "class SpriteManager {\n"
    # Convert all sprites in "Sprites_op/", while increasing their size times 2 if needed
    for filename in [_ for _ in os.listdir("Sprites_op/")]:
        print(f"Parsing '{filename}' ...")
        size = 2 # all sprites are enlarged except prepared exceptions such as digits and spacebar,reset messages
        if (filename in ["title_spacebar.png", "title_resetkey.png"]) or (filename.split(".")[0][:-1]=="digit"):
            size = 1
        spriteManagerJack += "" + Sprite_Parser("Sprites_op/"+filename, size).jack + "\n"
    spriteManagerJack += "}"
    # Pack-up and insert the 'SpriteManager.jack' into the project (folder above)
    with open("../SpriteManager.jack", "w+") as f:
            f.write(spriteManagerJack)

from PIL import Image

class Sprite_Parser:
    
    def __init__(self, filename, scale = 1, blackColorMask = 0, extendable = False, tabs = 1):
        
        # 1. Load the sprite image to parse from filepath 'filename'
        self._loadImage(filename)
        
        # 2. Upscale the image size times 'scale', maintaining aspect ratio
        self._upScale(scale)
        
        # 3. Load the color representing black as mask (all other non-mask colors are treated as white) 
        #    The color can be loaded either as (r,g,b) or from the pixels of input image as (x,y)
        #    If not specified, it will take first non-white pixel from input image as the mask
        self._loadMask(blackColorMask)
        
        # 4. Parse the pixels (read image as black/white based on mask)
        #    Returns '.jack' code as string (padded by 'tabs' tab spaces)
        #    'extendable' ? if 'True', generated draw method allows y-axis sprite tiling 
        self._parse_op(extendable, tabs)
    
    def _loadImage(self, filename):
        
        self.filename = filename.split("/")[1].split(".")[0]
        try:
            self.img = Image.open(f"{filename}")
        except:
            print(f"ERR: Couldn't load '_sprites/{filename}'")
            return;
        self.pixels = self.img.load()
        self.width, self.height = self.img.size
         
    def _upScale(self, scale):
        if type(scale)!=int or scale<=0:
            print(f"ERR: Invalid scale '{scale}'")
            return;
        if scale > 1:
            self.img = self.img.resize((self.width*scale,self.height*scale), Image.NEAREST)
            self.pixels = self.img.load()
            self.width, self.height = self.img.size
        self.scale = scale
        
    def _loadMask(self, mask):
        if type(mask)!=tuple or not len(mask) in [2,3]:
            for i in range(self.width):
                for j in range(self.height):
                    if self.pixels[i,j] != (255,255,255) and self.pixels[i,j] != (255,255,255,255):
                        self.mask = self.pixels[i,j]
                        return;
        elif len(mask)==3:
            self.mask = mask;
        elif len(mask)==2:
            self.mask = self.pixels[mask[0], mask[1]]
        else:
            print(f"Unexpected mask case ('_loadMask(self, {mask})')")
            exit()
        
    def _parse_op(self, extendable = False, tabs = 1):
        filename = f"{self.filename}"#_x{self.scale}"
        _output_jack  = "".join(["\t" for _ in range(tabs)]) + f"function void draw_{filename}" + ("(int location)" if not extendable else "(int location, int repeat)") + " {"+"\n" 
        _output_jack += "".join(["\t" for _ in range(tabs)]) + "\tvar int memAddress;"               +"\n"
        _output_jack += "".join(["\t" for _ in range(tabs)]) + "\tlet memAddress = 16384+location;"  +"\n"
        _output_jack += ("" if not extendable else "".join(["\t" for _ in range(tabs)]) + "\twhile (repeat > -1) {\n")
        for _i in range(0,self.width,16):
            _output_jack += ("" if not extendable else "\t") +"".join(["\t" for _ in range(tabs)]) + f"\t// sprite draw column_{_i//16}" +"\n"
            for j in range(self.height):
                segment_code = "";
                for segment in range(16):
                    i = _i + segment
                    if i >= self.width:
                        segment_code += "0"
                    else:   
                        if self.pixels[i,j] == self.mask:
                            self.pixels[i,j] = (0, 0 ,0)
                            segment_code += "1"
                        else:
                            self.pixels[i,j] = (255, 255, 255)
                            segment_code += "0"
                #print(segment_code.replace('0',' ').replace('1','█'))
                segment_code = segment_code[::-1]
                if segment_code[0] == "1":
                    segment_code = ((segment_code.replace("0",".")).replace("1","0")).replace(".","1");
                    _addr_val = -((int(segment_code,2)+1))
                else:
                    _addr_val = (int(segment_code,2))
                if not extendable:
                    _output_jack += "".join(["\t" for _ in range(tabs)]) + f"\tdo Memory.poke(memAddress+{j*32+_i//16}, {_addr_val});"+"\n"
                else:
                    _output_jack += "".join(["\t" for _ in range(tabs+1)]) + f"\tdo Memory.poke(memAddress+((repeat*{self.height*32})+{j*32+_i//16}), {_addr_val});"+"\n"     
        _output_jack += ("" if not extendable else "".join(["\t" for _ in range(tabs)]) + "\t\tlet repeat = repeat - 1;\n")
        _output_jack += ("" if not extendable else "".join(["\t" for _ in range(tabs)]) + "\t}\n")       
        _output_jack += "".join(["\t" for _ in range(tabs)]) + "\treturn; \n"
        _output_jack += "".join(["\t" for _ in range(tabs)]) + "} \n"
            
        self.img.save(f"_sprites_png/{filename}.png")
        with open(f"_sprites_jack/{filename}.jack", "w+") as f:
            f.write(_output_jack)
        self.jack = _output_jack
        
if __name__ == '__main__':
    main()