from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle
from datetime import date
import state

# ── Palette pastel ────────────────────────────────────────────────────────────
P_ROUGE  = (1.00, 0.85, 0.85, 1)
P_JAUNE  = (1.00, 0.97, 0.80, 1)
P_BLANC  = (0.98, 0.98, 0.98, 1)
P_GRIS   = (0.91, 0.91, 0.95, 1)
P_OPEN   = (0.95, 0.97, 1.00, 1)
P_OPEN_SUB  = (0.88, 0.92, 0.98, 1)
P_CLOSED    = (0.90, 0.97, 0.90, 1)
P_DISMISSED = (0.94, 0.90, 0.97, 1)

T_ROUGE   = (0.65, 0.15, 0.15, 1)
T_JAUNE   = (0.50, 0.38, 0.00, 1)
T_NORMAL  = (0.15, 0.15, 0.20, 1)
T_PARENT  = (0.20, 0.30, 0.55, 1)
T_SUB     = (0.25, 0.35, 0.60, 1)
T_CLOSED  = (0.20, 0.45, 0.20, 1)
T_DISMISS = (0.38, 0.20, 0.55, 1)

BLEU_BTN  = (0.35, 0.55, 0.85, 1)
VERT_BTN  = (0.25, 0.65, 0.35, 1)


def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return date(int(date_str[6:10]), int(date_str[3:5]), int(date_str[0:2]))
    except Exception:
        return None


def _actionable_color(task):
    due = _parse_date(task.due_str)
    today = date.today()
    if task.has_children:
        return P_GRIS, T_PARENT
    if due is None:
        return P_BLANC, T_NORMAL
    delta = (due - today).days
    if delta <= 0:
        return P_ROUGE, T_ROUGE
    if delta <= 15:
        return P_JAUNE, T_JAUNE
    return P_BLANC, T_NORMAL


def _is_actionable(task):
    if task.priority == 9 or task.fuzzy == 'someday':
        return False
    start = _parse_date(task.start_str)
    if start and start > date.today():
        return False
    return True


def _get_tasks(mode, tag_filter=None):
    if mode == 'closed':
        source = state.PAR_TAG_CLOSED
    elif mode == 'dismissed':
        source = state.PAR_TAG_DISMISSED
    else:
        source = state.PAR_TAG

    seen = set()
    taches = []
    tags_iter = [tag_filter] if tag_filter else list(source.keys())

    for tag in tags_iter:
        for task in source.get(tag, []):
            if task.task_uid in seen:
                continue
            seen.add(task.task_uid)
            if mode == 'actionable' and not _is_actionable(task):
                continue
            taches.append(task)

    def sort_key(t):
        due = _parse_date(t.due_str)
        return (0, due, t.title) if due else (1, date(9999, 12, 31), t.title)

    if mode == 'actionable':
        terminales = sorted([t for t in taches if not t.has_children], key=sort_key)
        parentes   = sorted([t for t in taches if t.has_children], key=sort_key)
        return terminales + parentes
    else:
        return sorted(taches, key=sort_key)


_TITRES = {'open': 'Ouvertes', 'actionable': 'Actionnables',
           'closed': 'Fermées', 'dismissed': 'Abandonnées'}
_VIDES  = {'open': 'Aucune tâche ouverte.',
           'actionable': 'Aucune tâche actionnable.',
           'closed': 'Aucune tâche fermée.',
           'dismissed': 'Aucune tâche abandonnée.'}


class ActionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tag_filter = None
        self._mode = 'open'
        self._expanded = False

    def load_view(self, mode='open', tag_filter=None):
        self._mode = mode
        if tag_filter is not None:
            self._tag_filter = tag_filter
        if mode != 'open':
            self._expanded = False
        self.build_ui()

    def _resolve_tag_filter(self, source):
        """Remet _tag_filter à None si le tag n'existe pas dans la source courante."""
        if self._tag_filter and self._tag_filter not in source:
            self._tag_filter = None

    def build_ui(self):
        self.clear_widgets()
        root = BoxLayout(orientation='vertical')

        # Résoudre la source selon le mode
        if self._mode == 'closed':
            source = state.PAR_TAG_CLOSED
        elif self._mode == 'dismissed':
            source = state.PAR_TAG_DISMISSED
        else:
            source = state.PAR_TAG

        # Vérifier que le tag filtré existe dans cette vue
        self._resolve_tag_filter(source)

        # ── HEADER : titre + rafraîchir + nouveau ─────────────────────────────
        header = BoxLayout(size_hint_y=None, height=55, padding=[5, 5])
        header.add_widget(Label(
            text='gtgDroid', bold=True, font_size=22,
            color=(0.20, 0.40, 0.75, 1)
        ))
        btn_refresh = Button(
            text='Rafraîchir', size_hint_x=0.35,
            background_color=BLEU_BTN, color=(1, 1, 1, 1), font_size=13
        )
        btn_refresh.bind(on_press=self.refresh)
        btn_new = Button(
            text='  +  ', size_hint_x=0.15,
            background_color=VERT_BTN, color=(1, 1, 1, 1),
            font_size=20, bold=True
        )
        btn_new.bind(on_press=self.go_to_new)
        header.add_widget(btn_refresh)
        header.add_widget(btn_new)
        root.add_widget(header)

        # ── BOUTONS DE VUE ────────────────────────────────────────────────────
        view_bar = BoxLayout(size_hint_y=None, height=45, spacing=3, padding=[5, 3])
        for label, mode in [('Ouvertes','open'), ('Actionnables','actionable'),
                             ('Fermées','closed'), ('Abandonnées','dismissed')]:
            active = self._mode == mode
            btn = Button(
                text=label,
                background_color=BLEU_BTN if active else (0.75, 0.78, 0.85, 1),
                color=(1, 1, 1, 1),
                font_size=13, bold=active
            )
            def on_press_view(x, m=mode):
                self.load_view(mode=m)
            btn.bind(on_press=on_press_view)
            view_bar.add_widget(btn)
        root.add_widget(view_bar)

        # ── FILTRES TAGS ──────────────────────────────────────────────────────

        if self._mode == 'actionable':
            tags_presents = sorted(t for t in source if any(_is_actionable(x) for x in source[t]))
        else:
            tags_presents = sorted(t for t in source if source[t])

        if tags_presents:
            filter_scroll = ScrollView(size_hint_y=None, height=42,
                                       do_scroll_y=False, do_scroll_x=True)
            filter_bar = BoxLayout(size_hint_x=None, height=42, spacing=4, padding=[5, 2])
            filter_bar.bind(minimum_width=filter_bar.setter('width'))

            def make_filter_btn(label, tag_val):
                active = self._tag_filter == tag_val
                btn = Button(
                    text=label, size_hint_x=None,
                    width=max(75, len(label) * 9 + 20), height=36,
                    background_color=(0.35, 0.58, 0.88, 1) if active else (0.82, 0.86, 0.94, 1),
                    color=(1, 1, 1, 1) if active else (0.20, 0.30, 0.55, 1),
                    font_size=13, bold=active
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

        # ── BOUTON DÉPLIER (mode open uniquement) ─────────────────────────────
        if self._mode == 'open':
            btn_expand = Button(
                text='▼ Tout déplier' if not self._expanded else '▲ Tout replier',
                size_hint_y=None, height=36,
                background_color=(0.88, 0.92, 0.98, 1),
                color=(0.20, 0.35, 0.65, 1), font_size=13
            )
            def toggle_expand(x):
                self._expanded = not self._expanded
                self.build_ui()
            btn_expand.bind(on_press=toggle_expand)
            root.add_widget(btn_expand)

        # ── LISTE ─────────────────────────────────────────────────────────────
        taches = _get_tasks(self._mode, self._tag_filter)

        scroll = ScrollView()
        layout = GridLayout(cols=1, spacing=2, size_hint_y=None, padding=[5, 5])
        layout.bind(minimum_height=layout.setter('height'))

        if not taches:
            layout.add_widget(Label(
                text=_VIDES.get(self._mode, 'Aucune tâche.'),
                size_hint_y=None, height=60,
                color=(0.5, 0.5, 0.5, 1), font_size=15
            ))
        elif self._mode == 'open':
            sous_uids = set()
            for t in taches:
                if t.has_children:
                    for sub in state.SUBTASKS_PAR_UID.get(t.task_uid, []):
                        sous_uids.add(sub.task_uid)
            racines = [t for t in taches if t.task_uid not in sous_uids]
            for task in racines:
                self._add_row(layout, task, indent=False)
                if task.has_children and self._expanded:
                    for sub in state.SUBTASKS_PAR_UID.get(task.task_uid, []):
                        self._add_row(layout, sub, indent=True)
        else:
            for task in taches:
                self._add_row(layout, task, indent=False)

        scroll.add_widget(layout)
        root.add_widget(scroll)

        # ── LÉGENDE actionnables ───────────────────────────────────────────────
        if self._mode == 'actionable':
            legende = BoxLayout(size_hint_y=None, height=28, padding=[10, 2], spacing=12)
            for bg, texte in [(P_ROUGE,'■ En retard'), (P_JAUNE,'■ Bientôt'),
                              (P_BLANC,'■ OK'), (P_GRIS,'■ Parent')]:
                legende.add_widget(Label(
                    text=texte, font_size=11,
                    color=(bg[0]*0.6, bg[1]*0.5, bg[2]*0.5, 1) if bg != P_BLANC
                    else (0.45, 0.45, 0.50, 1)
                ))
            root.add_widget(legende)

        self.add_widget(root)

    def _add_row(self, layout, task, indent=False):
        if self._mode == 'actionable':
            bg, fg = _actionable_color(task)
        elif self._mode == 'closed':
            bg, fg = P_CLOSED, T_CLOSED
        elif self._mode == 'dismissed':
            bg, fg = P_DISMISSED, T_DISMISS
        else:
            bg = P_OPEN_SUB if indent else P_OPEN
            fg = T_SUB if indent else (T_PARENT if task.has_children else T_NORMAL)

        hauteur = 44 if indent else 50

        row = BoxLayout(size_hint_y=None, height=hauteur)
        with row.canvas.before:
            Color(*bg)
            row._rect = Rectangle(pos=row.pos, size=row.size)
        row.bind(pos=lambda w, v: setattr(w._rect, 'pos', v))
        row.bind(size=lambda w, v: setattr(w._rect, 'size', v))

        if self._mode == 'closed':
            icone = '✓'
        elif self._mode == 'dismissed':
            icone = '✕'
        elif task.has_children:
            icone = '▶'
        else:
            icone = '○'

        due = _parse_date(task.due_str)
        today = date.today()
        if due:
            delta = (due - today).days
            if self._mode == 'actionable':
                if delta < 0:   due_txt = f'{abs(delta)}j retard'
                elif delta == 0: due_txt = 'Auj.'
                elif delta <= 15: due_txt = f'{delta}j'
                else:            due_txt = task.due_str
            else:
                due_txt = task.due_str
        else:
            due_txt = ''

        tags_autres = [t.strip() for t in task.tags.split(',')
                       if t.strip() and t.strip() != self._tag_filter] if task.tags else []
        tags_line = '  '.join(f'@{t}' for t in tags_autres)

        prefix = '        ' if indent else '  '
        ligne1 = f'{prefix}{icone}  {task.title}'
        texte = f'{ligne1}\n{prefix}   {tags_line}' if tags_line else ligne1

        btn = Button(
            text=texte, halign='left', valign='middle',
            text_size=(None, None), color=fg,
            background_color=(0, 0, 0, 0),
            font_size=13 if indent else 15
        )
        btn.bind(size=lambda w, v: setattr(w, 'text_size', (v[0] - 95, None)))
        btn.task_data = task
        btn.bind(on_press=self.go_to_detail)
        row.add_widget(btn)

        if due_txt:
            lbl = Label(
                text=due_txt, size_hint_x=None, width=85,
                color=fg, font_size=12, halign='right', valign='middle'
            )
            lbl.bind(size=lambda w, v: setattr(w, 'text_size', v))
            row.add_widget(lbl)

        layout.add_widget(row)

    def refresh(self, *args):
        from widgets import loading_popup
        from kivy.clock import Clock
        popup = loading_popup()
        def do_refresh(dt):
            from caldav_api import fetch_all
            fetch_all()
            popup.dismiss()
            self.build_ui()
        Clock.schedule_once(do_refresh, 0.1)

    def go_to_new(self, *args):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('new').load_form()
        self.manager.current = 'new'

    def go_to_detail(self, btn):
        task_data = btn.task_data
        state.CURRENT_TAG = task_data.tags.split(',')[0].strip() if task_data.tags else 'Sans tag'
        state.CURRENT_VIEW = self._mode
        self.manager.transition.direction = 'left'
        self.manager.get_screen('detail').load_task(task_data, from_screen='action')
        self.manager.current = 'detail'