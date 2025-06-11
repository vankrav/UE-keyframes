import unreal
import csv
import os

# Настройки секвенции
SEQUENCE_PATH = "/Game/Sequences/LightAnimation"  # Путь к секвенции в UE
FPS = 60  # Кадров в секунду
NUM_LIGHTS = 64  # Количество светильников
FIRST_LIGHT_INDEX = 0  # Начальный индекс светильников
# Получаем абсолютный путь к файлам
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DMX_PATH = os.path.join(SCRIPT_DIR, "New_Animation.chan")  # Путь к исходному DMX файлу
CSV_PATH = os.path.join(SCRIPT_DIR, "New_Animation.csv")  # Путь к CSV файлу
INTENSITY_MULTIPLIER = 1300.0  # Множитель интенсивности

def log(message):
    """Вспомогательная функция для логирования"""
    unreal.log(f"[DMX Import] {message}")
    print(f"[DMX Import] {message}")

def convert_dmx_to_csv(input_file, output_file):
    """Конвертирует DMX файл в CSV формат"""
    log(f"Converting DMX file: {input_file} -> {output_file}")
    
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
    
    log(f"Conversion completed! Created {frame_number} frames")

def import_dmx_to_sequencer():
    log("Starting DMX import process...")
    
    # Проверяем, нужно ли конвертировать DMX файл
    if not os.path.exists(CSV_PATH) or os.path.getmtime(DMX_PATH) > os.path.getmtime(CSV_PATH):
        log("CSV file doesn't exist or DMX file is newer. Converting...")
        if not os.path.exists(DMX_PATH):
            log(f"ERROR: DMX file not found: {DMX_PATH}")
            return None
        convert_dmx_to_csv(DMX_PATH, CSV_PATH)
    else:
        log("Using existing CSV file")
    
    log(f"CSV file path: {CSV_PATH}")
    
    # Загружаем или создаем секвенцию
    log("Loading or creating sequence...")
    sequence = unreal.load_asset(SEQUENCE_PATH, unreal.LevelSequence)
    if not sequence:
        log(f"Sequence not found at {SEQUENCE_PATH}, creating new one...")
        sequence = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            SEQUENCE_PATH.split('/')[-1],
            '/'.join(SEQUENCE_PATH.split('/')[:-1]),
            unreal.LevelSequence,
            unreal.LevelSequenceFactoryNew()
        )
    log("Sequence ready")
    
    # Читаем CSV файл
    log("Reading CSV file...")
    with open(CSV_PATH, 'r') as f:
        csv_reader = csv.reader(f)
        # Читаем заголовок и создаём карту <имя_колонки -> индекс>
        headers = next(csv_reader)
        header_indices = {h: idx for idx, h in enumerate(headers)}
        log(f"CSV headers detected: {headers}")

        # Считываем все оставшиеся строки как данные кадров
        frame_data = list(csv_reader)
    
    total_frames = len(frame_data)
    duration_seconds = total_frames / FPS
    log(f"Read {total_frames} frames from CSV")
    log(f"Animation duration will be {duration_seconds:.2f} seconds at {FPS} FPS")
    
    # Получаем все Spot Light актеры в сцене
    log("Getting editor subsystem...")
    world = unreal.EditorLevelLibrary.get_editor_world()
    log("Getting actors from level...")
    
    try:
        log("Getting all actors...")
        all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SpotLight)
        log(f"Found {len(all_actors)} spot lights")
    except Exception as e:
        log(f"Error getting actors: {str(e)}")
        return None
    
    spot_lights = {}
    
    # Находим все Spot Light актеры и сохраняем их в словарь
    log("Processing found actors...")
    for actor in all_actors:
        log(f"Processing actor: {actor.get_name()}")
        for i in range(NUM_LIGHTS):
            if actor.get_name() == f"SpotLight_{i}":
                spot_lights[i] = actor
                log(f"Matched SpotLight_{i}")
    
    log(f"Found {len(spot_lights)} matching spot lights in the scene")
    
    if not spot_lights:
        log("No matching spot lights found! Make sure you have SpotLight_0 through SpotLight_63 in your scene")
        return None
    
    # Устанавливаем частоту кадров для секвенции
    log(f"Setting sequence frame rate to {FPS} fps...")
    sequence.set_display_rate(unreal.FrameRate(FPS, 1))
    
    # Для каждого светильника создаем binding и track в секвенции
    log("Creating animation tracks...")
    total_lights = len(spot_lights)
    for light_idx, (light_index, light_actor) in enumerate(spot_lights.items(), 1):
        log(f"Processing SpotLight_{light_index} ({light_idx}/{total_lights})...")
        
        try:
            # Получаем LightComponent из актёра
            light_component = light_actor.get_component_by_class(unreal.LightComponent)
            if not light_component:
                log(f"No LightComponent found for SpotLight_{light_index}")
                continue
            
            # Получаем имя компонента
            component_name = light_component.get_name()
            log(f"Found light component: {component_name}")
                
            # Попробуем создать binding для компонента напрямую
            try:
                # Вариант 1: Binding для компонента
                binding = sequence.add_possessable(light_component)
                property_path = "Intensity"
                log(f"Created component binding for {component_name}")
            except:
                # Вариант 2: Binding для актёра с путём к компоненту
                binding = sequence.add_possessable(light_actor)
                property_path = f"{component_name}.Intensity"
                log(f"Created actor binding, will use path: {property_path}")
            
            log(f"Created binding for SpotLight_{light_index}")
            
            # Создаём трек для свойства Intensity
            intensity_track = binding.add_track(unreal.MovieSceneFloatTrack)
            intensity_track.set_property_name_and_path("Intensity", property_path)
            log(f"Created intensity track with path: {property_path}")
            
            # Создаем секцию для трека
            intensity_section = intensity_track.add_section()
            
            # Получаем канал через правильный метод
            channels = intensity_section.get_all_channels()
            if not channels:
                log(f"No channels found for SpotLight_{light_index}")
                continue
                
            intensity_channel = channels[0]
            log(f"Got channel for SpotLight_{light_index}")
            
            # Добавляем ключи для каждого кадра
            log(f"Adding {total_frames} keyframes for SpotLight_{light_index}...")
            frames_processed = 0
            for frame_num, frame_values in enumerate(frame_data):
                try:
                    # Получаем значение яркости для текущего светильника (0-1)
                    column_name = f"light_{light_index}"
                    if column_name not in header_indices:
                        # Если в CSV нет соответствующей колонки, пропускаем
                        continue
                    brightness_idx = header_indices[column_name]
                    if brightness_idx >= len(frame_values):
                        continue
                    brightness = float(frame_values[brightness_idx])
                    
                    # Создаем ключ на текущем кадре
                    frame_time = unreal.FrameNumber(frame_num)
                    intensity_channel.add_key(
                        frame_time,
                        brightness * INTENSITY_MULTIPLIER,
                        0.0,
                        unreal.MovieSceneTimeUnit.DISPLAY_RATE
                    )
                    frames_processed += 1
                    
                    # Показываем прогресс каждые 100 кадров
                    if frames_processed % 100 == 0:
                        log(f"Progress for SpotLight_{light_index}: {frames_processed}/{total_frames} frames")
                        
                except Exception as e:
                    log(f"Error adding keyframe {frame_num} for SpotLight_{light_index}: {str(e)}")
                    continue
            
            log(f"Finished adding {frames_processed} keyframes for SpotLight_{light_index}")
            
        except Exception as e:
            log(f"Error processing SpotLight_{light_index}: {str(e)}")
            continue
    
    log(f"Import completed! Created {total_frames} frames for {len(spot_lights)} lights")
    log(f"Total animation duration: {duration_seconds:.2f} seconds")
    return sequence

if __name__ == '__main__':
    import_dmx_to_sequencer() 