from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from datetime import date
import state

# ── Couleurs GTG ──────────────────────────────────────────────────────────────
ROUGE  = (0.95, 0.35, 0.35, 1)   # Échéance dépassée ou aujourd'hui
JAUNE  = (0.98, 0.85, 0.25, 1)   # Échéance dans les 15 prochains jours
BLANC  = (1,    1,    1,    1)    # Pas de date ou date lointaine
GRIS   = (0.88, 0.88, 0.88, 1)   # Tâche parente (a des enfants ouverts)

ROUGE_TXT = (0.7, 0.1, 0.1, 1)
JAUNE_TXT = (0.5, 0.4, 0.0, 1)
NOIR_TXT  = (0.15, 0.15, 0.15, 1)
GRIS_TXT  = (0.4,  0.4,  0.4,  1)


def _parse_date(date_str):
    """Convertit 'JJ/MM/AAAA' en date Python, None si vide ou invalide."""
    if not date_str:
        return None
    try:
        return date(int(date_str[6:10]), int(date_str[3:5]), int(date_str[0:2]))
    except Exception:
        return None


def _task_color(task):
    """Retourne (bg_color, txt_color) selon l'échéance — style GTG."""
    due = _parse_date(task.due_str)
    today = date.today()
    if task.has_children:
        return GRIS, GRIS_TXT
    if due is None:
        return BLANC, NOIR_TXT
    delta = (due - today).days
    if delta <= 0:
        return ROUGE, ROUGE_TXT
    if delta <= 15:
        return JAUNE, JAUNE_TXT
    return BLANC, NOIR_TXT


def _is_actionable(task):
    """Filtre GTG : exclut 'Un jour' et DTSTART dans le futur."""
    if task.priority == 9 or task.fuzzy == 'someday':
        return False
    start = _parse_date(task.start_str)
    if start and start > date.today():
        return False
    return True


def _get_actionable_tasks(tag_filter=None):
    """
    Retourne la liste plate de toutes les tâches actionnables,
    triées : d'abord les terminales (sans enfants) par échéance,
    puis les parentes (avec enfants ouverts) en dessous.
    Filtre optionnel par tag.
    """
    seen = set()
    terminales = []
    parentes = []

    source = state.PAR_TAG
    tags_a_parcourir = [tag_filter] if tag_filter else list(source.keys())

    for tag in tags_a_parcourir:
        for task in source.get(tag, []):
            if task.task_uid in seen:
                continue
            seen.add(task.task_uid)
            if not _is_actionable(task):
                continue
            if task.has_children:
                parentes.append(task)
            else:
                terminales.append(task)

    def sort_key(t):
        due = _parse_date(t.due_str)
        if due is None:
            return (1, date(9999, 12, 31), t.title)
        return (0, due, t.title)

    terminales.sort(key=sort_key)
    parentes.sort(key=sort_key)
    return terminales + parentes


class ActionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tag_filter = None

    def load_view(self, tag_filter=None):
        """Point d'entrée — construit l'écran avec filtre tag optionnel."""
        self._tag_filter = tag_filter
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation='vertical')

        # ── HEADER ────────────────────────────────────────────────────────────
        header = BoxLayout(size_hint_y=None, height=55, padding=[5, 5])
        btn_back = Button(
            text='←',
            size_hint_x=None, width=50,
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1),
            font_size=20
        )
        btn_back.bind(on_press=self.go_back)
        header.add_widget(btn_back)

        titre = '⚡ Actionnables'
        if self._tag_filter:
            titre += f'  #{self._tag_filter}'
        header.add_widget(Label(
            text=titre,
            bold=True, font_size=18,
            color=(0.2, 0.5, 0.9, 1)
        ))

        btn_refresh = Button(
            text='↺',
            size_hint_x=None, width=50,
            background_color=(0.2, 0.5, 0.9, 1),
            color=(1, 1, 1, 1),
            font_size=18
        )
        btn_refresh.bind(on_press=lambda x: self.build_ui())
        header.add_widget(btn_refresh)
        root.add_widget(header)

        # ── FILTRES TAGS ──────────────────────────────────────────────────────
        # Bouton "Tous" + un bouton par tag existant dans les actionnables
        tags_presents = sorted(set(
            tag for tag in state.PAR_TAG.keys()
            if any(_is_actionable(t) for t in state.PAR_TAG[tag])
        ))

        if tags_presents:
            filter_scroll = ScrollView(
                size_hint_y=None, height=45,
                do_scroll_y=False, do_scroll_x=True
            )
            filter_bar = BoxLayout(
                size_hint_x=None, height=45, spacing=4, padding=[5, 3]
            )
            filter_bar.bind(minimum_width=filter_bar.setter('width'))

            def make_filter_btn(label, tag_val):
                is_active = self._tag_filter == tag_val
                btn = Button(
                    text=label,
                    size_hint_x=None,
                    width=max(80, len(label) * 10 + 20),
                    height=39,
                    background_color=(0.2, 0.5, 0.9, 1) if is_active else (0.8, 0.8, 0.8, 1),
                    color=(1, 1, 1, 1) if is_active else (0.2, 0.2, 0.2, 1),
                    font_size=13,
                    bold=is_active
                )
                def on_press(x, v=tag_val):
                    self._tag_filter = v
                    self.build_ui()
                btn.bind(on_press=on_press)
                return btn

            filter_bar.add_widget(make_filter_btn('Tous', None))
            for tag in tags_presents:
                filter_bar.add_widget(make_filter_btn(f'#{tag}', tag))

            filter_scroll.add_widget(filter_bar)
            root.add_widget(filter_scroll)

        # ── LISTE DES TÂCHES ──────────────────────────────────────────────────
        taches = _get_actionable_tasks(self._tag_filter)

        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=2, size_hint_y=None, padding=[5, 5])
        layout.bind(minimum_height=layout.setter('height'))

        if not taches:
            layout.add_widget(Label(
                text='Aucune tâche actionnable.',
                size_hint_y=None, height=60,
                color=(0.5, 0.5, 0.5, 1),
                font_size=15
            ))
        else:
            for task in taches:
                self._add_task_row(layout, task)

        scroll.add_widget(layout)
        root.add_widget(scroll)

        # ── LÉGENDE ───────────────────────────────────────────────────────────
        legende = BoxLayout(size_hint_y=None, height=30, padding=[10, 2], spacing=15)
        for couleur, texte in [
            (ROUGE, '■ En retard'),
            (JAUNE, '■ Bientôt'),
            (BLANC, '■ OK'),
            (GRIS,  '■ Parent'),
        ]:
            lbl = Label(
                text=texte, font_size=11,
                color=(couleur[0]*0.6, couleur[1]*0.6, couleur[2]*0.6, 1)
                if couleur != BLANC else (0.5, 0.5, 0.5, 1)
            )
            legende.add_widget(lbl)
        root.add_widget(legende)

        self.add_widget(root)

    def _add_task_row(self, layout, task):
        bg_color, txt_color = _task_color(task)
        due = _parse_date(task.due_str)
        today = date.today()

        # Ligne principale
        row = BoxLayout(size_hint_y=None, height=52, padding=[8, 4])

        with row.canvas.before:
            Color(*bg_color)
            row._rect = Rectangle(pos=row.pos, size=row.size)
        row.bind(pos=lambda w, v: setattr(w._rect, 'pos', v))
        row.bind(size=lambda w, v: setattr(w._rect, 'size', v))

        # Icône parente ou terminale
        icone = '▶ ' if task.has_children else '○ '

        # Texte échéance
        if due:
            delta = (due - today).days
            if delta < 0:
                due_txt = f'{abs(delta)}j de retard'
            elif delta == 0:
                due_txt = "Aujourd'hui"
            elif delta <= 15:
                due_txt = f'dans {delta}j'
            else:
                due_txt = task.due_str
        else:
            due_txt = ''

        # Titre + tags
        tags_str = task.tags
        tags_autres = [t.strip() for t in tags_str.split(',')
                       if t.strip() and t.strip() != self._tag_filter] if tags_str else []
        tags_display = '  '.join(f'@{t}' for t in tags_autres) if tags_autres else ''

        titre_complet = f'{icone}{task.title}'
        if tags_display:
            titre_complet += f'\n  {tags_display}'

        btn = Button(
            text=titre_complet,
            halign='left', valign='middle',
            text_size=(None, None),
            color=txt_color,
            background_color=(0, 0, 0, 0),
            font_size=15 if not task.has_children else 14,
            bold=not task.has_children
        )
        btn.bind(size=lambda w, v: setattr(w, 'text_size', (v[0] - 10, None)))
        btn.task_data = task
        btn.bind(on_press=self.go_to_detail)
        row.add_widget(btn)

        if due_txt:
            lbl_due = Label(
                text=due_txt,
                size_hint_x=None, width=90,
                color=txt_color,
                font_size=12,
                halign='right', valign='middle'
            )
            lbl_due.bind(size=lambda w, v: setattr(w, 'text_size', v))
            row.add_widget(lbl_due)

        layout.add_widget(row)

    def go_to_detail(self, btn):
        task_data = btn.task_data
        state.CURRENT_TAG = task_data.tags.split(',')[0].strip() if task_data.tags else 'Sans tag'
        self.manager.transition.direction = 'left'
        detail = self.manager.get_screen('detail')
        detail.load_task(task_data)
        self.manager.current = 'detail'

    def go_back(self, *args):
        self.manager.transition.direction = 'right'
        self.manager.current = 'tags'
