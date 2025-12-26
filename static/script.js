document.addEventListener('DOMContentLoaded', function() {
    const setReminderForm = document.getElementById('setReminderForm');
    const remindersList = document.getElementById('remindersList');

    async function loadReminders() {
        const resp = await fetch('/api/get_reminders');
        if (resp.status === 401) return;
        const reminders = await resp.json();
        remindersList.innerHTML = reminders.length ? '' : '<p>Напоминаний нет.</p>';
        reminders.forEach(r => {
            const div = document.createElement('div');
            div.className = 'card reminder-item';
            div.innerHTML = `<div><h4>${r.med_name}</h4><p class="time">${r.time}</p><small>Слот: ${r.slot}</small></div>
                             <button class="btn-icon" onclick="deleteReminder(${r.id})">❌</button>`;
            remindersList.appendChild(div);
        });
    }

    if (setReminderForm) {
        setReminderForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                med_name: document.getElementById('med_name').value,
                reminder_time: document.getElementById('reminder_time').value,
                reminder_email: document.getElementById('reminder_email').value,
                frequency: document.getElementById('frequency').value,
                slot: document.getElementById('slot').value
            };
            await fetch('/api/set_reminder', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            setReminderForm.reset();
            loadReminders();
        });
        loadReminders();
    }

    window.deleteReminder = async (id) => {
        if (confirm('Удалить?')) {
            await fetch(`/api/delete_reminder/${id}`, {method: 'POST'});
            loadReminders();
        }
    };
});
