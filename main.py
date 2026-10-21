"""Запуск: python main.py. Визуальные проверки: python tools/smoke_test.py."""
import argparse
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description="Snake 3D — маленькое путешествие")
    parser.add_argument("--offscreen",action="store_true",help="Рендер без видимого окна")
    parser.add_argument("--save-path",type=Path,help="Отдельный профиль для проверки")
    parser.add_argument("--smoke-frames",type=int,default=0,help="Закрыть после N кадров (для проверки сборки)")
    parser.add_argument("--screenshot",type=Path,help="Сохранить кадр перед закрытием")
    parser.add_argument("--mute",action="store_true",help="Отключить аудиодрайвер при диагностике")
    parser.add_argument("--self-test",action="store_true",help="Проверить меню, уровни и сохранения с временным профилем")
    args=parser.parse_args()
    if args.self_test:
        from tools.smoke_test import run
        run(windowed=not args.offscreen)
        return
    from game.app import SnakeApp
    app=SnakeApp(offscreen=args.offscreen,save_path=args.save_path,audio=not args.mute)
    if args.smoke_frames:
        def stop(task):
            if task.frame>=args.smoke_frames:
                if args.screenshot:
                    from game.resources import screenshot
                    screenshot(app.win,args.screenshot)
                app.userExit()
                return task.done
            return task.cont
        app.taskMgr.add(stop,"bounded-smoke")
    app.run()


if __name__=="__main__":
    main()
