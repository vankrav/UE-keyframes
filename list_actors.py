import unreal

def log(message):
    """Вспомогательная функция для логирования"""
    unreal.log(f"[Actor List] {message}")
    print(f"[Actor List] {message}")

def list_light_properties(light_obj):
    """Выводит все свойства объекта"""
    properties = []
    for prop in dir(light_obj):
        if not prop.startswith('_'):  # Пропускаем внутренние свойства
            try:
                value = getattr(light_obj, prop)
                if not callable(value):  # Пропускаем методы
                    properties.append(f"{prop}: {value}")
            except Exception:
                continue
    return properties

def list_all_lights():
    """Выводит информацию только о светильниках"""
    log("Getting all lights in the scene...")
    
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        all_lights = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SpotLight)
        
        log(f"Found {len(all_lights)} spot lights")
        log("=== Listing all spot lights ===")
        
        # Берем только первый светильник для детального анализа
        if all_lights:
            light = all_lights[0]
            light_name = light.get_name()
            log(f"Analyzing light: '{light_name}'")
            
            # Получаем компонент светильника
            try:
                light_component = light.light_component
                if light_component:
                    comp_name = light_component.get_name()
                    log(f"Component name: '{comp_name}'")
                    
                    # Выводим все свойства компонента
                    log("Component properties:")
                    properties = list_light_properties(light_component)
                    for prop in properties:
                        log(f"  {prop}")
                    
                    # Пробуем получить значение интенсивности разными способами
                    try:
                        intensity = light_component.intensity
                        log(f"Direct intensity access: {intensity}")
                    except Exception as e:
                        log(f"Error accessing intensity directly: {str(e)}")
                    
                    try:
                        intensity = getattr(light_component, "intensity", None)
                        log(f"Intensity via getattr: {intensity}")
                    except Exception as e:
                        log(f"Error accessing intensity via getattr: {str(e)}")
            except Exception as e:
                log(f"Error analyzing light component: {str(e)}")
            
        log("=== End of analysis ===")
        
    except Exception as e:
        log(f"Error: {str(e)}")

if __name__ == '__main__':
    list_all_lights() 