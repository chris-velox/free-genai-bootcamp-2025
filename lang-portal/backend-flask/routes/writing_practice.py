from flask import request, jsonify
from flask_cors import cross_origin
import random
from manga_ocr import MangaOcr
import base64
import io
from PIL import Image
import numpy as np
from kana_dictionary import ROMAJI_TO_HIRAGANA, ROMAJI_TO_KATAKANA

# Initialize manga_ocr outside the routes for efficiency
mocr = MangaOcr()

def get_kana_dict(kana_type):
    """Helper function to get the appropriate kana dictionary"""
    # Invert the dictionaries since we want kana->romaji mapping
    if kana_type == 'hiragana':
        return {v: k for k, v in ROMAJI_TO_HIRAGANA.items()}
    return {v: k for k, v in ROMAJI_TO_KATAKANA.items()}

def load(app):
    @app.route('/writing-practice/random-kana', methods=['GET'])
    @cross_origin()
    def get_random_kana():
        """Get a random kana-romaji pair based on the specified type"""
        kana_type = request.args.get('type', 'hiragana').lower()
        
        if kana_type not in ['hiragana', 'katakana']:
            return jsonify({'error': 'Invalid kana type'}), 400

        kana_dict = get_kana_dict(kana_type)
        
        # Get a random kana-romaji pair
        kana = random.choice(list(kana_dict.keys()))
        romaji = kana_dict[kana]

        return jsonify({
            'kana': kana,
            'romaji': romaji
        })

    @app.route('/writing-practice/verify-kana', methods=['POST'])
    @cross_origin()
    def verify_kana():
        """Verify the drawn kana using manga-ocr"""
        try:
            data = request.json
            if not all(k in data for k in ['image', 'expectedKana', 'expectedRomaji', 'kanaType']):
                return jsonify({'error': 'Missing required fields'}), 400

            # Convert base64 image to PIL Image
            image_data = data['image'].split(',')[1]
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to grayscale
            image = image.convert('L')
            image_array = np.array(image)

            # Find the bounding box with more aggressive thresholding
            threshold = 200  # More aggressive threshold for better isolation
            rows = np.any(image_array < threshold, axis=1)
            cols = np.any(image_array < threshold, axis=0)
            ymin, ymax = np.where(rows)[0][[0, -1]]
            xmin, xmax = np.where(cols)[0][[0, -1]]
            
            # Calculate center and make a square crop
            center_y = (ymin + ymax) // 2
            center_x = (xmin + xmax) // 2
            size = max(ymax - ymin, xmax - xmin)
            padding = size // 2  # Add 50% padding
            
            # Ensure square crop with padding
            crop_size = size + 2 * padding
            ymin = max(0, center_y - crop_size // 2)
            ymax = min(image_array.shape[0], center_y + crop_size // 2)
            xmin = max(0, center_x - crop_size // 2)
            xmax = min(image_array.shape[1], center_x + crop_size // 2)
            
            # Crop and create square image
            cropped_array = image_array[ymin:ymax, xmin:xmax]
            
            # Create white background square image
            square_size = max(cropped_array.shape)
            square_array = np.full((square_size, square_size), 255, dtype=np.uint8)
            
            # Center the cropped image in the square
            y_offset = (square_size - cropped_array.shape[0]) // 2
            x_offset = (square_size - cropped_array.shape[1]) // 2
            square_array[
                y_offset:y_offset + cropped_array.shape[0],
                x_offset:x_offset + cropped_array.shape[1]
            ] = cropped_array

            # Convert to PIL and resize
            processed_image = Image.fromarray(square_array)
            processed_image = processed_image.resize((200, 200), Image.Resampling.LANCZOS)

            # Enhance contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(processed_image)
            processed_image = enhancer.enhance(2.5)  # Increased contrast

            # Debug: Save processed image
            processed_image.save('debug_image.png')
            print("Saved debug image to debug_image.png")

            # Use manga-ocr to recognize the character
            recognized_text = mocr(processed_image)
            print("Raw recognized text:", recognized_text)

            # Post-process the recognized text:
            # 1. Take only the first character if multiple are detected
            # 2. Remove any punctuation or special characters
            import unicodedata
            recognized_text = ''.join(char for char in recognized_text if unicodedata.category(char).startswith('Lo'))
            if len(recognized_text) > 0:
                recognized_text = recognized_text[0]  # Take only the first character
            
            print("Processed recognized text:", recognized_text)
            print("Expected kana:", data['expectedKana'])
            
            # Compare with expected kana
            success = recognized_text == data['expectedKana']

            return jsonify({
                'success': success,
                'recognized': recognized_text,
                'debug_info': {
                    'image_size': processed_image.size,
                    'bounding_box': {
                        'xmin': int(xmin),
                        'xmax': int(xmax),
                        'ymin': int(ymin),
                        'ymax': int(ymax)
                    }
                }
            })

        except Exception as e:
            print("Error processing image:", str(e))
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500 