import csv

def convert_dmx_to_csv(input_file, output_file):
    # Читаем входной файл
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Подготавливаем заголовки для CSV
    headers = ['frame'] + [f'light_{i}' for i in range(64)]  # Добавляем столбец frame
    
    # Открываем выходной CSV файл
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)  # Записываем заголовки
        
        # Обрабатываем каждую строку
        frame_number = 0  # Счетчик кадров
        for line in lines:
            # Пропускаем комментарии и пустые строки
            if line.startswith('#') or not line.strip():
                continue
                
            # Разбиваем строку на значения
            values = line.strip().split()
            
            # Конвертируем значения из 0-255 в 0-1
            normalized_values = [float(val) / 255.0 for val in values]
            
            # Добавляем номер кадра в начало строки
            row_data = [frame_number] + normalized_values
            
            # Записываем данные в CSV
            writer.writerow(row_data)
            
            frame_number += 1  # Увеличиваем счетчик кадров

if __name__ == '__main__':
    convert_dmx_to_csv('DMX64.chan', 'DMX64.csv') 