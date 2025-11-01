import logging
import time
from other_file import summmm

# Настраиваем логгер
logging.basicConfig(
    level=logging.DEBUG, # Уровень вывода сообщений (DEBUG показывает всё)
 ##   filename="example.log",
    format='%(asctime)s [%(levelname)s]: %(message)s', # Формат записи
    datefmt='%Y-%m-%d %H:%M:%S' # Формат даты-времени
)

logger = logging.getLogger('my_logger')






def main():

    i = 0
    try:
        while True:
            logger.debug(f'Итерация {i}')
            summmm(i,6);
            if i % 3 == 0:
                logger.info(f'Это итерация номер {i}, мы проверили её!')
                
            elif i % 5 == 0 and i != 0:
                logger.warning(f'Осторожно, число делится на 5: {i}')
            
            else:
                logger.error(f'Ошибка: не обработанная ситуация на итерации {i}')
        
            i += 1
            time.sleep(1)  # Пауза в одну секунду
    
    except KeyboardInterrupt:
        logger.critical("Прервано пользователем")

if __name__ == "__main__":
    main()