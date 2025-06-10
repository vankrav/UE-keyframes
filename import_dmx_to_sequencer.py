import unreal
import csv

# Настройки секвенции
SEQUENCE_PATH = "/Game/Sequences/LightAnimation"  # Путь к секвенции в UE
FPS = 60  # Кадров в секунду
NUM_LIGHTS = 64  # Количество светильников
CSV_PATH = "DMX64.csv"  # Путь к CSV файлу

def import_dmx_to_sequencer():
    # Загружаем или создаем секвенцию
    sequence = unreal.load_asset(SEQUENCE_PATH, unreal.LevelSequence)
    if not sequence:
        sequence = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            SEQUENCE_PATH.split('/')[-1],
            '/'.join(SEQUENCE_PATH.split('/')[:-1]),
            unreal.LevelSequence,
            unreal.LevelSequenceFactoryNew()
        )
    
    # Читаем CSV файл
    with open(CSV_PATH, 'r') as f:
        csv_reader = csv.reader(f)
        headers = next(csv_reader)  # Пропускаем заголовки
        frame_data = list(csv_reader)
    
    # Получаем все Point Light актеры в сцене
    editor_subsystem = unreal.get_editor_subsystem()
    all_actors = editor_subsystem.get_all_level_actors()
    point_lights = {}
    
    # Находим все Point Light актеры и сохраняем их в словарь
    for actor in all_actors:
        if isinstance(actor, unreal.PointLight):
            for i in range(NUM_LIGHTS):
                if actor.get_actor_label() == f"PointLight{i}":
                    point_lights[i] = actor
    
    # Для каждого светильника создаем binding и track в секвенции
    for light_index, light_actor in point_lights.items():
        # Добавляем binding для светильника
        binding = sequence.add_possessable(light_actor)
        
        # Создаем трек для свойства Intensity
        intensity_track = binding.add_track(unreal.MovieSceneFloatTrack)
        intensity_track.set_property_name_and_path("Intensity", "Intensity")
        
        # Создаем секцию для трека
        intensity_section = intensity_track.add_section()
        intensity_channel = intensity_section.get_channels_by_type(unreal.MovieSceneScriptingFloatChannel)[0]
        
        # Добавляем ключи для каждого кадра
        for frame_num, frame_values in enumerate(frame_data):
            # Получаем значение яркости для текущего светильника (0-1)
            brightness = float(frame_values[light_index])
            
            # Создаем ключ на текущем кадре
            frame_time = unreal.FrameNumber(frame_num)
            intensity_channel.add_key(
                frame_time,
                brightness * 5000.0,  # Умножаем на 5000, так как Intensity в UE обычно использует большие значения
                0.0,  # субкадр
                unreal.MovieSceneTimeUnit.DISPLAY_RATE
            )
    
    print(f"Импорт завершен! Создано {len(frame_data)} кадров для {len(point_lights)} светильников.")
    return sequence

if __name__ == '__main__':
    import_dmx_to_sequencer() 