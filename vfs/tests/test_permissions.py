# vfs/tests/test_permissions.py
import unittest
from vfs.core.fs import SistemaArchivos, PermError, NotFound

class TestPermisosVFS(unittest.TestCase):
    def setUp(self):
        self.fs = SistemaArchivos()
        # Preparar directorio de trabajo para usuario1
        self.fs.su('usuario1')
        self.fs.cd('/home/usuario1')

    def test_dueno_puede_escribir_y_otro_no(self):
        # usuario1 crea un archivo y escribe
        self.assertEqual(self.fs.touch('secreto.txt'), 'Archivo secreto.txt creado')
        self.assertEqual(self.fs.echo('secreto.txt', 'hola'), '4 bytes escritos')

        # usuario2 intenta escribir -> debe fallar por permisos (rw-r-----)
        self.fs.su('usuario2')
        self.fs.cd('/home/usuario1')
        with self.assertRaises(PermError):
            self.fs.echo('secreto.txt', 'edicion no autorizada')

        # lectura también debe fallar (no tiene 'r' en grupo/otros)
        with self.assertRaises(PermError):
            _ = self.fs.cat('secreto.txt')

    def test_root_puede_escribir_siempre(self):
        self.fs.touch('solo_root.txt')
        # Volver a root
        self.fs.su('root')
        self.fs.cd('/home/usuario1')
        # root puede escribir sin restricción
        self.assertEqual(self.fs.echo('solo_root.txt', 'root edit'), '9 bytes escritos')

    def test_cambiar_permisos_para_permitir_a_otros(self):
        # Crear como usuario1
        self.fs.touch('compartido.txt')
        # Por defecto: 'rw-r-----' (otros no pueden)
        # Dejar que grupo tenga escritura: 'rw-rw----' (simplificación del modelo)
        self.fs.chmod('compartido.txt', 'rw-rw----')

        # Cambiar a usuario2 e intentar escribir: en este modelo simplificado
        # _check_write permite si hay 'w' en la sección de grupo (3:6),
        # sin validar membresía real de grupo (supuesto educativo).
        self.fs.su('usuario2')
        self.fs.cd('/home/usuario1')
        self.assertEqual(self.fs.echo('compartido.txt', 'escritura grupo'), '15 bytes escritos')

    def test_archivo_no_existe(self):
        with self.assertRaises(NotFound):
            self.fs.echo('fantasma.txt', 'nada')

if __name__ == '__main__':
    unittest.main()
