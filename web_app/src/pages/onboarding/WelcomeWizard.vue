<template>
    <q-page padding>
        <div class="wizard-shell q-mx-auto">
            <!-- ── Slim top row: mascot · progress rail · skip escape ────
                 The three elements sit inline with generous horizontal
                 spacing. The persistent "Skip onboarding" hatch lives here
                 (it replaced the old sign-out button in the layout header),
                 except on the finish step where the Finish action takes
                 over. ────────────────────────────────────────────────── -->
            <div class="wizard-topbar q-mb-lg">
                <q-avatar square size="40px" class="wizard-mascot">
                    <img src="../../assets/logo-mascot.png" alt="Dora" />
                </q-avatar>
                <OnboardingStepRail
                    class="wizard-topbar-rail"
                    :sections="railSections"
                    :active-section="view"
                    :active-index="railActiveIndex"
                    @jump="onRailJump"
                />
                <BaseButton
                    v-if="!(view === 'setup' && isLastStep)"
                    variant="ghost"
                    dense
                    class="wizard-skip dora-text-secondary"
                    :icon="ICONS.skip_next"
                    label="Skip onboarding"
                    :loading="completing"
                    @click="onSkipEverything"
                />
            </div>

            <!-- ══ STORY — cinematic intro + the hero loop ══════════════ -->
            <OnboardingStory
                v-if="view === 'story'"
                v-model:scene-index="storySceneIndex"
                @enter-setup="enterSetup"
            />

            <!-- ══ SETUP — the steps (draft-until-finish; applied on Finish) ══ -->
            <template v-else>
            <q-banner v-if="loadError" class="dora-bg-negative-soft text-negative q-mb-md" dense rounded>
                {{ loadError }}
            </q-banner>

            <!-- ── Step 1: Welcome — say hello, pick a face, pick a look ──
                 Owner 2026-10-17: the old card (mascot + blurb over two bare
                 selects) "looks absolutely horrible". Rebuilt as a hero that
                 previews the user's own avatar, a profile-picture picker
                 (upload or one of the pre-made food pictures), and visual
                 theme cards in place of the Theme select (each card paints a
                 mock-up in its own theme's tokens; the wizard itself stays on
                 WelcomeLayout's pinned dark canvas, so there's no live
                 preview). Everything is still a draft applied on Finish (L35). ──────────────────────────────── -->
            <div v-show="currentStep?.id === 'welcome'" class="welcome-step q-mb-md">
                <section class="welcome-hero">
                    <div class="welcome-hero__avatar">
                        <ImageEditTile
                            :label="hasDraftAvatar || currentUser?.has_image
                                ? 'Change your profile picture'
                                : 'Upload a profile picture'"
                            :width="104"
                            :height="104"
                            @pick="onUploadAvatar"
                            @error="(m) => (avatarError = m)"
                        >
                            <q-avatar v-if="hasDraftAvatar" size="104px">
                                <img :src="form.avatarDataUrl ?? ''" alt="Your profile picture" />
                            </q-avatar>
                            <UserAvatar
                                v-else-if="currentUser"
                                :user-id="currentUser.user_id"
                                :has-image="currentUser.has_image"
                                size="104px"
                                fallback="initials"
                                :username="currentUser.username"
                                color="accent"
                                text-color="dark"
                            />
                        </ImageEditTile>
                        <img
                            src="../../assets/logo-mascot.png"
                            alt=""
                            class="welcome-hero__mascot"
                            aria-hidden="true"
                        />
                    </div>
                    <div class="welcome-hero__copy">
                        <div class="welcome-hero__kicker">Hi, I'm Dora</div>
                        <h1 class="welcome-hero__title">
                            Nice to meet you{{ currentUser?.username ? `, ${currentUser.username}` : '' }}.
                        </h1>
                        <p class="welcome-hero__blurb">
                            I keep your pantry, shopping and cooking in one place so
                            the weekly shop stops feeling like detective work. Let's
                            make Dora yours. It takes about a minute.
                        </p>
                    </div>
                </section>

                <section class="welcome-panel">
                    <div class="welcome-panel__head">
                        <div class="welcome-panel__title">Pick a profile picture</div>
                        <div class="welcome-panel__sub">
                            Tap one of ours, or tap your avatar above to upload a photo.
                        </div>
                    </div>
                    <PresetAvatarPicker
                        :selected-key="form.avatarPresetKey"
                        @pick="onPickPresetAvatar"
                        @error="(m) => (avatarError = m)"
                    />
                    <div v-if="avatarError || hasDraftAvatar" class="welcome-panel__foot">
                        <span v-if="avatarError" class="text-caption text-negative">{{ avatarError }}</span>
                        <q-space />
                        <BaseButton
                            v-if="hasDraftAvatar"
                            variant="ghost"
                            dense
                            :icon="ICONS.undo"
                            label="Undo"
                            @click="clearDraftAvatar"
                        />
                    </div>
                </section>

                <section class="welcome-panel">
                    <div class="welcome-panel__head">
                        <div class="welcome-panel__title">Look &amp; feel</div>
                        <div class="welcome-panel__sub">
                            More themes live in Settings → Appearance.
                        </div>
                    </div>
                    <div class="welcome-themes" role="radiogroup" aria-label="Theme">
                        <button
                            v-for="opt in THEME_OPTIONS"
                            :key="opt.value"
                            type="button"
                            role="radio"
                            class="welcome-theme"
                            :class="{ 'welcome-theme--active': form.theme === opt.value }"
                            :aria-checked="form.theme === opt.value"
                            @click="form.theme = opt.value"
                        >
                            <span class="welcome-theme__preview" aria-hidden="true">
                                <span
                                    v-for="themeKey in opt.previews"
                                    :key="themeKey"
                                    class="welcome-theme__half"
                                    :data-theme="themeKey"
                                >
                                    <span class="welcome-theme__bar" />
                                    <span class="welcome-theme__line" />
                                    <span class="welcome-theme__line welcome-theme__line--short" />
                                    <span class="welcome-theme__dot" />
                                </span>
                            </span>
                            <span class="welcome-theme__label">
                                <q-icon :name="opt.icon" size="18px" />
                                {{ opt.label }}
                            </span>
                            <q-icon
                                v-if="form.theme === opt.value"
                                :name="ICONS.check_circle"
                                size="20px"
                                class="welcome-theme__badge"
                            />
                        </button>
                    </div>
                    <div class="welcome-font">
                        <div class="welcome-font__label">Font</div>
                        <DoraSegmented
                            :model-value="form.fontFamily"
                            :options="FONT_OPTIONS"
                            @update:model-value="(v) => (form.fontFamily = v)"
                        />
                    </div>
                    <!-- FU-615 — household headcount + cook-style ("I batch-cook")
                         are install-wide settings (Settings → System → Cooking);
                         batch cooking is offered on the features step instead. -->
                </section>
            </div>

            <!-- ── Step 2: Admin bootstrap (first user only) ──────────── -->
            <q-card
                v-show="currentStep?.id === 'admin'"
                flat
                bordered
                class="q-mb-md"
            >
                <q-card-section>
                    <div class="text-h6 q-mb-sm">You're the admin</div>
                    <div class="text-body2 dora-text-secondary q-mb-md">
                        First user on a fresh install gets the admin role
                        automatically, so all the global settings (stores,
                        stock levels, user management) are unlocked for you
                        out of the gate. There's nothing to change here, but
                        a couple of pointers:
                    </div>
                    <q-list bordered class="rounded-borders">
                        <q-item>
                            <q-item-section avatar>
                                <q-icon :name="ICONS.storefront" color="primary" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Curate the stores you shop at</q-item-label>
                                <q-item-label caption>
                                    Settings → Stores. Add the stores you actually
                                    use; upload a logo so they're recognisable.
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                        <q-item>
                            <q-item-section avatar>
                                <q-icon :name="ICONS.people" color="primary" />
                            </q-item-section>
                            <q-item-section>
                                <q-item-label>Invite teammates later</q-item-label>
                                <q-item-label caption>
                                    Settings → Users. Sharing is opt-in;
                                    a solo household never needs it.
                                </q-item-label>
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
            </q-card>

            <!-- ── Step: Build your Dora experience (first user only) ──────
                 Owner 2026-10-17. The install-wide features as cards; a tap
                 flips one on or off. Seeded from the install's current
                 settings and applied on Finish with the rest of the draft
                 (L35), so a bail changes nothing. Every card is a real admin
                 toggle that also lives in Settings → System. ──────────── -->
            <div v-show="currentStep?.id === 'features'" class="features-step q-mb-md">
                <div class="features-step__head">
                    <div class="text-h6">Build your Dora experience</div>
                    <div class="text-body2 dora-text-secondary">
                        Switch on the parts your household wants. You can change
                        any of these later.
                    </div>
                </div>
                <div class="feature-grid">
                    <button
                        v-for="feature in FEATURE_CARDS"
                        :key="feature.key"
                        type="button"
                        role="switch"
                        class="feature-card"
                        :class="{ 'feature-card--on': featurePicks[feature.key] }"
                        :aria-checked="featurePicks[feature.key]"
                        :disabled="!featuresLoaded"
                        @click="featurePicks[feature.key] = !featurePicks[feature.key]"
                    >
                        <span class="feature-card__icon" aria-hidden="true">
                            <q-icon :name="feature.icon" size="24px" />
                        </span>
                        <span class="feature-card__body">
                            <span class="feature-card__title">{{ feature.title }}</span>
                            <span class="feature-card__desc">{{ feature.description }}</span>
                        </span>
                        <span class="feature-card__state">
                            <q-icon
                                :name="featurePicks[feature.key] ? ICONS.check_circle : ICONS.circle_outline"
                                size="22px"
                            />
                            <span class="feature-card__state-label">
                                {{ featurePicks[feature.key] ? 'On' : 'Off' }}
                            </span>
                        </span>
                    </button>
                </div>
                <div v-if="!featuresLoaded" class="text-caption dora-text-muted q-mt-sm">
                    Loading your install's current settings…
                </div>
            </div>

            <!-- ── Step 3: Seed catalogues ──────────────────────────── -->
            <!-- the two default-catalogue cards are expansions so
                 the user can pick individual names, not just all-or-none.
                 Master checkbox on each expansion header is tri-state:
                 unchecked = none picked, indeterminate = some, checked =
                 all. Clicking it toggles all names on/off. Individual
                 rows toggle themselves. -->
            <div
                v-show="currentStep?.id === 'seed'"
                class="row q-col-gutter-md q-mb-md"
            >
                <div class="col-12 col-md-6">
                    <q-card flat bordered class="seed-card"
                        :class="{ 'seed-card--picked': groupPickCount > 0 }">
                        <q-expansion-item :model-value="groupPickCount > 0">
                            <template #header>
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.category" size="28px" color="primary" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label class="text-subtitle1">
                                        Use Dora's default stock groups
                                    </q-item-label>
                                    <q-item-label caption class="dora-text-muted">
                                        {{ groupPickCount }} of {{ catalog?.groups?.length ?? 0 }} chosen
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section side>
                                    <q-checkbox
                                        :model-value="groupMasterState"
                                        toggle-indeterminate
                                        @update:model-value="toggleAllGroups($event)"
                                        @click.stop
                                    />
                                </q-item-section>
                            </template>
                            <q-list dense>
                                <q-item
                                    v-for="name in catalog?.groups ?? []"
                                    :key="name"
                                    tag="label"
                                    dense
                                >
                                    <q-item-section>
                                        <q-item-label>{{ name }}</q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <q-checkbox v-model="groupPicks[name.toLowerCase()]" />
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-expansion-item>
                    </q-card>
                </div>
                <div class="col-12 col-md-6">
                    <q-card flat bordered class="seed-card"
                        :class="{ 'seed-card--picked': locationPickCount > 0 }">
                        <q-expansion-item :model-value="locationPickCount > 0">
                            <template #header>
                                <q-item-section avatar>
                                    <q-icon :name="ICONS.place" size="28px" color="primary" />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label class="text-subtitle1">
                                        Use Dora's default locations
                                    </q-item-label>
                                    <q-item-label caption class="dora-text-muted">
                                        {{ locationPickCount }} of {{ locationLeafPaths.length }} chosen
                                    </q-item-label>
                                </q-item-section>
                                <q-item-section side>
                                    <q-checkbox
                                        :model-value="locationMasterState"
                                        toggle-indeterminate
                                        @update:model-value="toggleAllLocations($event)"
                                        @click.stop
                                    />
                                </q-item-section>
                            </template>
                            <q-list dense>
                                <template v-for="zone in catalog?.locations ?? []" :key="zone.name">
                                    <q-item tag="label" dense>
                                        <q-item-section>
                                            <q-item-label>{{ zone.name }}</q-item-label>
                                            <q-item-label caption class="dora-text-muted">Zone</q-item-label>
                                        </q-item-section>
                                        <q-item-section side>
                                            <q-checkbox v-model="locationPicks[zone.name.toLowerCase()]" />
                                        </q-item-section>
                                    </q-item>
                                    <q-item
                                        v-for="child in zone.children"
                                        :key="`${zone.name}/${child.name}`"
                                        tag="label"
                                        dense
                                        class="q-pl-lg"
                                    >
                                        <q-item-section>
                                            <q-item-label>{{ child.name }}</q-item-label>
                                            <q-item-label caption class="dora-text-muted">
                                                Under {{ zone.name }}
                                            </q-item-label>
                                        </q-item-section>
                                        <q-item-section side>
                                            <q-checkbox
                                                v-model="locationPicks[`${zone.name}/${child.name}`.toLowerCase()]"
                                            />
                                        </q-item-section>
                                    </q-item>
                                </template>
                            </q-list>
                        </q-expansion-item>
                    </q-card>
                </div>

                <!-- inline "paste rows" affordance so bulk
                     ingest doesn't demand a nav-out to the full importer.
                     Rows queue into draftItems and flow through the
                     existing seed-items pipeline on Finish, after the
                     groups/locations seed lands (so group/location names
                     resolve). Full spreadsheet importer still one click
                     away for anything richer. -->
                <div class="col-12">
                    <q-expansion-item
                        icon="content_paste"
                        label="Paste rows to bulk-add items"
                        caption="One per line: Name, Group?, Location?"
                        class="seed-paste"
                    >
                        <div class="q-pa-sm">
                            <q-input
                                v-model="pasteRowsText"
                                type="textarea"
                                outlined
                                dense
                                autogrow
                                :input-style="{ minHeight: '110px' }"
                                placeholder="Milk, Dairy, Fridge
Olive oil, Pantry
Toilet paper, Toiletries, Bathroom"
                            />
                            <div class="row items-center justify-between q-mt-sm">
                                <div class="text-caption dora-text-muted">
                                    <template v-if="pasteRowsParsed.length > 0">
                                        {{ pasteRowsParsed.length }} row{{ pasteRowsParsed.length === 1 ? '' : 's' }}
                                        ready, added on Finish.
                                    </template>
                                    <template v-else-if="pasteRowsText.trim().length > 0">
                                        Every row needs at least a name.
                                    </template>
                                    <template v-else>
                                        Group + location are optional. Unknown names create
                                        an item without a group or location.
                                    </template>
                                </div>
                                <BaseButton
                                    variant="ghost"
                                    class="text-primary"
                                    :disable="pasteRowsParsed.length === 0"
                                    :label="`Queue ${pasteRowsParsed.length || ''} row${pasteRowsParsed.length === 1 ? '' : 's'}`"
                                    @click="queuePastedRows"
                                />
                            </div>
                        </div>
                    </q-expansion-item>
                </div>

                <div class="col-12 text-caption dora-text-muted q-mt-xs">
                    Bringing in a full spreadsheet?
                    <router-link to="/settings/admin/data/import" class="text-primary">
                        Open the full importer instead →
                    </router-link>
                </div>

                <!-- opt-in demo dataset. Plain rows (no
                     `is_demo` marking) so the user deletes them like any
                     other recipe / item / plan if they aren't useful. -->
                <div class="col-12">
                    <q-card
                        flat
                        bordered
                        class="seed-card"
                        :class="{ 'seed-card--picked': form.seedDemo }"
                        @click="form.seedDemo = !form.seedDemo"
                    >
                        <q-card-section class="row items-center">
                            <q-icon :name="ICONS.restaurant_menu" size="28px" class="q-mr-sm" color="primary" />
                            <div class="col">
                                <div class="text-subtitle1">Add a demo recipe + this-week meal plan</div>
                                <div class="text-caption dora-text-muted">
                                    Off by default. Creates a working
                                    "Spaghetti Aglio e Olio" recipe (with the
                                    three pantry items it needs) and schedules
                                    it for dinner this week, so the cookbook +
                                    planner aren't empty on first open.
                                    Rename or delete it like any other entry.
                                </div>
                            </div>
                            <q-checkbox v-model="form.seedDemo" @click.stop />
                        </q-card-section>
                    </q-card>
                </div>

                <!-- Starter packs (L37) — tick a pack to add its common items. -->
                <div v-if="(catalog?.packs?.length ?? 0) > 0" class="col-12">
                    <div class="text-subtitle1 q-mt-sm">Starter packs</div>
                    <div class="text-caption dora-text-muted q-mb-sm">
                        Tick a pack to add its common items (already grouped + located).
                        Expand one to choose individual items.
                    </div>
                    <q-list bordered class="rounded-borders">
                        <q-expansion-item
                            v-for="pack in catalog?.packs ?? []"
                            :key="pack.key"
                        >
                            <template #header>
                                <q-item-section avatar>
                                    <q-checkbox
                                        :model-value="packState(pack)"
                                        toggle-indeterminate
                                        @update:model-value="togglePack(pack, $event)"
                                        @click.stop
                                    />
                                </q-item-section>
                                <q-item-section>
                                    <q-item-label>{{ pack.label }}</q-item-label>
                                    <q-item-label caption>
                                        {{ pack.blurb }} ·
                                        {{ packSelectedCount(pack) }}/{{ pack.items.length }} chosen
                                    </q-item-label>
                                </q-item-section>
                            </template>
                            <q-list>
                                <q-item
                                    v-for="item in pack.items"
                                    :key="item.name"
                                    tag="label"
                                    dense
                                >
                                    <q-item-section>
                                        <q-item-label>{{ item.name }}</q-item-label>
                                        <q-item-label
                                            v-if="item.group || item.location"
                                            caption
                                        >
                                            {{ [item.group, item.location].filter(Boolean).join(' · ') }}
                                        </q-item-label>
                                    </q-item-section>
                                    <q-item-section side>
                                        <q-checkbox v-model="packItemSelected[item.name]" />
                                    </q-item-section>
                                </q-item>
                            </q-list>
                        </q-expansion-item>
                    </q-list>
                </div>
            </div>

            <!-- ── Step 4: First stock item ─────────────────────────── -->
            <q-card
                v-show="currentStep?.id === 'first_item'"
                flat
                bordered
                class="q-mb-md"
            >
                <q-card-section>
                    <div class="text-h6 q-mb-sm">Add your first stock item</div>
                    <div class="text-body2 dora-text-secondary q-mb-md">
                        Pick a staple you always have on hand. You can add the
                        rest later.
                    </div>
                    <q-form @submit.prevent="onAddFirstItem" class="q-gutter-md">
                        <q-input
                            v-model="firstItem.name"
                            outlined
                            dense
                            label="Name"
                            placeholder="e.g. Milk, Olive oil, Pasta"
                            autofocus
                            :rules="[(v: string) => !!v || 'Give it a name']"
                        />
                        <div class="row q-col-gutter-sm">
                            <q-select
                                v-model="firstItem.group_name"
                                outlined
                                dense
                                label="Group"
                                :options="groupNameOptions"
                                clearable
                                class="col-12 col-sm-6"
                            />
                            <q-select
                                v-model="firstItem.location_name"
                                outlined
                                dense
                                label="Location"
                                :options="locationNameOptions"
                                clearable
                                class="col-12 col-sm-6"
                            />
                        </div>
                        <div class="row justify-end q-gutter-sm">
                            <BaseButton
                                variant="ghost"
                                class="dora-text-secondary"
                                label="I'll do this later"
                                @click="advance"
                            />
                            <BaseButton
                                variant="primary"
                                :icon="ICONS.add"
                                :label="draftItems.length > 0
                                    ? `Add another (${draftItems.length} added)`
                                    : 'Add stock item'"
                                type="submit"
                            />
                        </div>
                    </q-form>

                    <!-- Slim "added" list (L36) — the queued first items. -->
                    <q-list
                        v-if="draftItems.length > 0"
                        bordered
                        class="rounded-borders q-mt-md"
                    >
                        <q-item-label header class="q-pb-xs">
                            Added ({{ draftItems.length }}), saved when you finish
                        </q-item-label>
                        <q-item v-for="(item, idx) in draftItems" :key="idx">
                            <q-item-section>
                                <q-item-label>{{ item.name }}</q-item-label>
                                <q-item-label
                                    v-if="item.group_name || item.location_name"
                                    caption
                                >
                                    {{ [item.group_name, item.location_name].filter(Boolean).join(' · ') }}
                                </q-item-label>
                            </q-item-section>
                            <q-item-section side>
                                <BaseButton
                                    variant="icon"
                                    :icon="ICONS.delete"
                                    aria-label="Remove"
                                    @click="removeDraftItem(idx)"
                                />
                            </q-item-section>
                        </q-item>
                    </q-list>
                </q-card-section>
            </q-card>

            <!-- ── Step: Finish — celebrate, recap, first steps ─────────
                 Owner 2026-10-17: "make the finishing page as useful and
                 polished as you can". Three parts: a hero that greets the
                 user with the face they just picked; a recap of exactly what
                 Finish will apply (the wizard is draft-until-finish, so this
                 is the last look before it lands); and "first steps" tiles,
                 each of which finishes and opens that screen. The loop recap
                 stays out — the hero loop already plays in Story. -->
            <div
                v-show="currentStep?.id === 'finish'"
                class="finish-step q-mb-md"
            >
                <OnboardingConfetti v-if="currentStep?.id === 'finish'" />
                <section class="finish-hero">
                    <div class="finish-hero__faces" aria-hidden="true">
                        <q-avatar v-if="hasDraftAvatar" size="72px" class="finish-hero__avatar">
                            <img :src="form.avatarDataUrl ?? ''" alt="" />
                        </q-avatar>
                        <UserAvatar
                            v-else-if="currentUser"
                            class="finish-hero__avatar"
                            :user-id="currentUser.user_id"
                            :has-image="currentUser.has_image"
                            size="72px"
                            fallback="initials"
                            :username="currentUser.username"
                            color="accent"
                            text-color="dark"
                        />
                        <DoraMascot mood="super_excited" :size="84" class="finish-hero__mascot" />
                    </div>
                    <div class="finish-hero__title">
                        You're all set{{ currentUser?.username ? `, ${currentUser.username}` : '' }}!
                    </div>
                    <div class="finish-hero__sub">
                        Tap Finish to save everything, or jump straight into one of
                        the first steps below.
                    </div>
                </section>

                <section v-if="finishRecap.length > 0" class="finish-panel">
                    <div class="finish-panel__title">What Finish will set up</div>
                    <ul class="finish-recap">
                        <li v-for="row in finishRecap" :key="row.key" class="finish-recap__row">
                            <span class="finish-recap__icon" aria-hidden="true">
                                <q-icon :name="row.icon" size="18px" />
                            </span>
                            <span class="finish-recap__text">{{ row.text }}</span>
                            <BaseButton
                                v-if="row.step !== undefined"
                                variant="ghost"
                                dense
                                size="sm"
                                class="dora-text-secondary"
                                label="Change"
                                @click="stepIndex = row.step"
                            />
                        </li>
                    </ul>
                </section>

                <section class="finish-panel">
                    <div class="finish-panel__title">First steps</div>
                    <div class="finish-tiles">
                        <button
                            v-for="(card, i) in flowCards"
                            :key="card.path"
                            type="button"
                            class="finish-tile"
                            :disabled="completing"
                            @click="onShowMe(card.path)"
                        >
                            <span class="finish-tile__icon" aria-hidden="true">
                                <q-icon :name="card.icon" size="22px" />
                            </span>
                            <span class="finish-tile__body">
                                <span class="finish-tile__title">
                                    <span v-if="card.numbered" class="finish-tile__num">{{ i + 1 }}</span>
                                    {{ card.title }}
                                </span>
                                <span class="finish-tile__desc">{{ card.description }}</span>
                            </span>
                            <q-icon :name="ICONS.chevron_right" size="20px" class="finish-tile__chevron" />
                        </button>
                    </div>
                </section>

                <section class="finish-tip">
                    <q-icon :name="ICONS.chat_bubble_outline" size="20px" class="finish-tip__icon" />
                    <span>
                        Stuck? Dora's help bubble follows you around the app, and the
                        <router-link to="/help" class="text-primary" @click.prevent="onShowMe('/help')">guides</router-link>
                        explain each area in depth.
                    </span>
                </section>
            </div>

            <!-- ── Footer: Back / Next ──────────────────────────────── -->
            <div class="row items-center q-mt-md">
                <BaseButton
                    variant="ghost"
                    :icon="ICONS.arrow_back"
                    :label="stepIndex === 0 ? 'Back to intro' : 'Back'"
                    @click="onBack"
                />
                <q-space />
                <BaseButton
                    variant="primary"
                    :icon-right="isLastStep ? 'check' : 'arrow_forward'"
                    :label="isLastStep ? 'Finish' : 'Next'"
                    :loading="completing"
                    @click="advance"
                />
            </div>
            </template>
        </div>
    </q-page>
</template>

<script lang="ts" setup>
    import { ICONS } from 'src/style/icons';
    import BaseButton from 'src/components/BaseButton.vue';
    import ImageEditTile from 'src/components/ImageEditTile.vue';
    import PresetAvatarPicker from 'src/components/PresetAvatarPicker.vue';
    import UserAvatar from 'src/components/UserAvatar.vue';
    import DoraMascot from 'src/components/dora/DoraMascot.vue';
    import DoraSegmented from 'src/components/settings/DoraSegmented.vue';
    import OnboardingConfetti from 'src/components/onboarding/OnboardingConfetti.vue';
    import OnboardingStepRail from 'src/components/onboarding/OnboardingStepRail.vue';
    import OnboardingStory from 'src/pages/onboarding/OnboardingStory.vue';
    import { storeToRefs } from 'pinia';
    import { useQuasar } from 'quasar';
    import { fontFamilyOptions, coalesceFontFamily } from 'src/services/themeService';
    import type { ProcessedImage } from 'src/services/files/imageService';
    import AppSettingsApiService, {
        type AppSettings,
        type UpdateAppSettingsCommand,
    } from 'src/services/api/appSettingsApiService';
    import { useFeatureFlags } from 'src/composables/useFeatureFlags';
    import type { FontFamilyPreference, ThemePreference } from 'src/models/auth';
    import type {
        OnboardingCatalog,
        OnboardingState,
        StarterPack,
        StarterPackItem,
    } from 'src/models/onboarding';
    import { NARRATIVE_SCENES } from 'src/pages/onboarding/onboardingContent';
    import type { StockGroup } from 'src/models/stockGroup';
    import OnboardingApiService from 'src/services/api/onboardingApiService';
    import StockGroupApiService from 'src/services/api/stockGroupApiService';
    import { extractFieldErrors } from 'src/services/errorHandling/apiErrorHandler';
    import { useAuthStore } from 'src/stores/authStore';
    import { useStockLocationStore } from 'src/stores/stockLocationStore';
    import { computed, onMounted, reactive, ref, watch } from 'vue';
    import { useRouter } from 'vue-router';

    const $q = useQuasar();
    const router = useRouter();
    const onboardingApi = new OnboardingApiService();
    const stockGroupApi = new StockGroupApiService();
    const appSettingsApi = new AppSettingsApiService();
    const { refresh: refreshFeatureFlags, money: moneyFlag } = useFeatureFlags();
    const authStore = useAuthStore();
    const stockLocationStore = useStockLocationStore();

    const { currentUser } = storeToRefs(authStore);

    // Stock groups don't have a store of their own; load them locally.
    const stockGroups = ref<StockGroup[]>([]);
    async function loadStockGroups() {
        try {
            stockGroups.value = await stockGroupApi.getAllAsync();
        } catch {
            stockGroups.value = [];
        }
    }

    // ── Static option lists ──────────────────────────────────────────
    // L28 — onboarding offers only System / Light / Dark. Light maps to the
    // brand light theme (Pesto) and Dark to Pesto Dark; the rest of the
    // palette catalogue (lemon-tart, blueberry, …) is pickable later in
    // Preferences. Values are real ThemePreference keys so we persist the
    // resolved theme rather than the legacy 'light'/'dark' aliases.
    //
    // 2026-10-17 — drawn as cards rather than a select. `previews` names the
    // theme(s) each card's mini mock-up is painted in: the halves carry a
    // `data-theme` attribute, so they read that theme's real tokens rather
    // than a copied palette (R-002). System shows both, split.
    const THEME_OPTIONS: {
        label: string;
        value: ThemePreference;
        icon: string;
        previews: string[];
    }[] = [
        { label: 'System', value: 'system', icon: ICONS.brightness_auto, previews: ['pesto', 'pesto-dark'] },
        { label: 'Light', value: 'pesto', icon: ICONS.light_mode, previews: ['pesto'] },
        { label: 'Dark', value: 'pesto-dark', icon: ICONS.dark_mode, previews: ['pesto-dark'] },
    ];
    // Font options + the `coalesceFontFamily` fold are the shared FU-614 source
    // in themeService (R-003). The wizard uses the full "Plus Jakarta Sans" label
    // (it has room), so no override.
    const FONT_OPTIONS = fontFamilyOptions();
    // ── Wizard step state ────────────────────────────────────────────
    type StepId =
        | 'welcome' | 'admin' | 'features'
        | 'seed' | 'first_item' | 'finish';
    type Step = { id: StepId; title: string };

    const state = ref<OnboardingState | null>(null);
    const loadError = ref<string | null>(null);
    const stepIndex = ref(0);
    const completing = ref(false);

    // ── Story / Setup view model (C-5.2) ─────────────────────────────
    // Two sections with instant, non-linear cross-jump via the shared rail.
    const view = ref<'story' | 'setup'>('story');
    const storySceneIndex = ref(0);

    // Two tracks. First user of an install (fresh self-host or first user in a
    // new SaaS household) walks the full setup — admin bootstrap, seed the
    // household-scoped groups/locations/catalogues, add a first stock item.
    // Every subsequent user joins an already-configured household, so they only
    // set personal prefs (display name / theme / font / headcount on the
    // welcome step) and land in the app.
    const visibleSteps = computed<Step[]>(() => {
        const steps: Step[] = [{ id: 'welcome', title: 'Welcome' }];
        if (state.value?.first_user) {
            steps.push({ id: 'admin', title: "You're the admin" });
            steps.push({ id: 'features', title: 'Build your Dora' });
            steps.push({ id: 'seed', title: 'Seed catalogues' });
            steps.push({ id: 'first_item', title: 'First stock item' });
        }
        steps.push({ id: 'finish', title: "You're all set" });
        return steps;
    });

    // ── Finish "first steps" (C-5.6, rebuilt 2026-10-17) ─────────────
    // The loop in the order a new household walks it, numbered, then the
    // optional extras. Each tile finishes onboarding and lands on its screen.
    // Price history only shows when spend tracking will be on — after Finish
    // it'd be a dead end otherwise (P3 Honest).
    const flowCards = computed(() => {
        const cards: {
            path: string;
            title: string;
            description: string;
            icon: string;
            numbered: boolean;
        }[] = [
            { path: '/stock', title: 'Stock your pantry', numbered: true,
              description: 'Add what you keep, with levels, locations and expiry.',
              icon: ICONS.inventory_2 },
            { path: '/cookbook', title: 'Fill your cookbook', numbered: true,
              description: 'See what you can cook from what’s in, then cook it step by step.',
              icon: ICONS.menu_book },
            { path: '/meal-plans', title: 'Plan the week', numbered: true,
              description: 'Plan meals and turn the week into a shopping list.',
              icon: ICONS.event },
            { path: '/shopping-lists', title: 'Go shopping', numbered: true,
              description: 'Lists build themselves from what’s low or out; finishing a shop restocks you.',
              icon: ICONS.shopping_cart },
        ];
        if (willHaveMoney.value) {
            cards.push({
                path: '/price-history', title: 'Watch your prices', numbered: false,
                description: 'See how what you pay moves over time.',
                icon: ICONS.savings,
            });
        }
        cards.push({
            path: '/settings/voice', title: "Pick Dora's voice", numbered: false,
            description: "A voice for Dora's chat replies and cook mode.",
            icon: ICONS.record_voice_over,
        });
        return cards;
    });

    const currentStep = computed<Step | null>(
        () => visibleSteps.value[stepIndex.value] ?? null,
    );
    const isLastStep = computed(
        () => stepIndex.value === visibleSteps.value.length - 1,
    );

    // ── Shared rail model (Story scenes + Setup steps) ───────────────
    // Nothing is gated — every dot is a jump target across both sections.
    const railSections = computed(() => [
        {
            key: 'story',
            label: 'Story',
            dots: NARRATIVE_SCENES.map((s) => ({
                key: s.id,
                label: s.kicker ?? s.headline,
            })),
        },
        {
            key: 'setup',
            label: 'Setup',
            dots: visibleSteps.value.map((s) => ({ key: s.id, label: s.title })),
        },
    ]);
    const railActiveIndex = computed(() =>
        view.value === 'story' ? storySceneIndex.value : stepIndex.value,
    );
    function onRailJump(sectionKey: string, index: number) {
        if (sectionKey === 'story') {
            view.value = 'story';
            storySceneIndex.value = index;
        } else {
            view.value = 'setup';
            stepIndex.value = index;
        }
    }
    function enterSetup() {
        view.value = 'setup';
    }

    // ── Form state (persists to localStorage so refresh resumes) ─────
    type WizardDraft = {
        theme: ThemePreference;
        fontFamily: FontFamilyPreference;
        // FU-615 — headcount + batch cook-style are install-wide settings now
        // (Settings → System → Cooking), no longer collected per-user here.
        // the seed-catalogue master booleans are gone; the
        // per-name pick sets below carry the same signal. A card is
        // effectively "on" when any name in it is picked, "off" when
        // none. See groupPicks / locationPicks below.
        // optional demo dataset (one recipe + a current-week meal
        // plan). Default off because it inserts plain rows the user then
        // has to clean up if they didn't actually want demo content.
        seedDemo: boolean;
        stepIndex: number;
        // 2026-10-17 — profile picture, drafted like everything else and
        // saved on Finish. `avatarDataUrl` is the encoded picture (an upload
        // or a rendered preset); `avatarPresetKey` only drives the picker's
        // selected ring and is null for an upload.
        avatarDataUrl: string | null;
        avatarPresetKey: string | null;
    };

    // A first stock item the user queued — created on Finish (L35), never
    // on each Add, so a mid-wizard bail leaves nothing behind.
    type DraftItem = {
        name: string;
        group_name: string | null;
        location_name: string | null;
    };

    const DRAFT_KEY = (userId: string) =>
        `dora.onboarding.draft.${userId || 'anonymous'}`;

    const form = reactive<WizardDraft>({
        theme: 'system',
        fontFamily: 'default',
        seedDemo: false,
        stepIndex: 0,
        avatarDataUrl: null,
        avatarPresetKey: null,
    });

    // ── Profile picture (welcome step) ───────────────────────────────
    const avatarError = ref<string | null>(null);
    const hasDraftAvatar = computed(() => !!form.avatarDataUrl);
    function onUploadAvatar(processed: ProcessedImage) {
        avatarError.value = null;
        form.avatarDataUrl = processed.dataUrl;
        form.avatarPresetKey = null;
    }
    function onPickPresetAvatar({ key, dataUrl }: { key: string; dataUrl: string }) {
        avatarError.value = null;
        form.avatarDataUrl = dataUrl;
        form.avatarPresetKey = key;
    }
    function clearDraftAvatar() {
        form.avatarDataUrl = null;
        form.avatarPresetKey = null;
    }

    // ── Build your Dora experience (features step, first user only) ──
    // Each card is one install-wide AppSetting the admin can also flip in
    // Settings → System. The pick is the plain on/off the card shows; the
    // mapping onto the setting lives in `apply`, so a richer stored value
    // (nutrition 'complex', auto-add 'all') that reads as "on" survives an
    // untouched card — `changedFeatureSettings` only sends what moved.
    type FeatureKey = 'money' | 'nutrition' | 'stocktake' | 'batch' | 'auto_add' | 'scanning';
    type FeatureCard = {
        key: FeatureKey;
        title: string;
        description: string;
        icon: string;
        read: (s: AppSettings) => boolean;
        apply: (on: boolean) => UpdateAppSettingsCommand;
    };
    const FEATURE_CARDS: readonly FeatureCard[] = [
        {
            key: 'money', title: 'Spend tracking', icon: ICONS.savings,
            description: 'Prices, budgets and what each meal costs.',
            read: (s) => s.money_enabled,
            apply: (on) => ({ money_enabled: on }),
        },
        {
            key: 'nutrition', title: 'Nutrition', icon: ICONS.monitor_heart,
            description: 'Calories and macros on your recipes and meal plans.',
            read: (s) => s.nutrition_mode !== 'off',
            apply: (on) => ({ nutrition_mode: on ? 'simple' : 'off' }),
        },
        {
            key: 'stocktake', title: 'Stocktakes', icon: ICONS.fact_check,
            description: 'Gentle reminders to check what’s really in the cupboard.',
            read: (s) => s.stocktake_enabled,
            apply: (on) => ({ stocktake_enabled: on }),
        },
        {
            key: 'auto_add', title: 'Auto-add essentials', icon: ICONS.add_shopping_cart,
            description: 'Essentials go on the shopping list the moment they run low.',
            read: (s) => s.auto_add_mode !== 'off',
            apply: (on) => ({ auto_add_mode: on ? 'essential_only' : 'off' }),
        },
        {
            key: 'batch', title: 'Batch cooking', icon: ICONS.mealsPrepared,
            description: 'Cook once, eat for days: Dora tracks the leftovers.',
            read: (s) => s.batch_features_enabled,
            apply: (on) => ({ batch_features_enabled: on }),
        },
        {
            key: 'scanning', title: 'Barcodes & QR labels', icon: ICONS.qr_code_scanner,
            description: 'Scan products and print QR labels for your shelves.',
            read: (s) => s.scanning_enabled,
            apply: (on) => ({ scanning_enabled: on }),
        },
    ];
    const featurePicks = reactive<Record<FeatureKey, boolean>>({
        money: false, nutrition: false, stocktake: true,
        auto_add: true, batch: false, scanning: false,
    });
    // What the install says right now — the baseline `featurePicks` is
    // diffed against on Finish. Null until loaded (non-admins never load it).
    const featureBaseline = ref<Record<FeatureKey, boolean> | null>(null);
    const featuresLoaded = computed(() => featureBaseline.value !== null);
    // Picks restored from a saved draft win over the install's values.
    let savedFeaturePicks: Partial<Record<FeatureKey, boolean>> | null = null;

    async function loadFeatureBaseline() {
        if (!state.value?.first_user || !currentUser.value?.is_admin) return;
        try {
            const settings = await appSettingsApi.getAsync();
            const baseline = {} as Record<FeatureKey, boolean>;
            for (const card of FEATURE_CARDS) baseline[card.key] = card.read(settings);
            featureBaseline.value = baseline;
            Object.assign(featurePicks, baseline, savedFeaturePicks ?? {});
        } catch {
            // Leave the step unloaded (cards disabled); Finish then sends
            // nothing for it and the admin can use Settings instead.
        }
    }
    const changedFeatureSettings = computed<UpdateAppSettingsCommand>(() => {
        const base = featureBaseline.value;
        if (!base) return {};
        const out: UpdateAppSettingsCommand = {};
        for (const card of FEATURE_CARDS) {
            if (featurePicks[card.key] !== base[card.key]) {
                Object.assign(out, card.apply(featurePicks[card.key]));
            }
        }
        return out;
    });
    const willHaveMoney = computed(() =>
        featureBaseline.value ? featurePicks.money : moneyFlag.value,
    );

    // ── Finish recap — what Finish is about to apply ─────────────────
    // Built from the same draft `applyDraft` reads, so it can't promise
    // something Finish won't do. `step` lets each row jump back to change it.
    function stepIndexOf(id: StepId): number | undefined {
        const i = visibleSteps.value.findIndex((st) => st.id === id);
        return i >= 0 ? i : undefined;
    }
    function plural(n: number, one: string, many = `${one}s`): string {
        return `${n} ${n === 1 ? one : many}`;
    }
    const finishRecap = computed(() => {
        const rows: { key: string; icon: string; text: string; step?: number | undefined }[] = [];
        if (hasDraftAvatar.value) {
            rows.push({ key: 'avatar', icon: ICONS.person, text: 'Your new profile picture',
                step: stepIndexOf('welcome') });
        }
        const themeLabel = THEME_OPTIONS.find((o) => o.value === form.theme)?.label;
        if (themeLabel) {
            rows.push({ key: 'look', icon: ICONS.palette, step: stepIndexOf('welcome'),
                text: `${themeLabel} theme, ${FONT_OPTIONS.find((o) => o.value === form.fontFamily)?.label ?? 'default'} font` });
        }
        if (featureBaseline.value) {
            const on = FEATURE_CARDS.filter((c) => featurePicks[c.key]).map((c) => c.title);
            rows.push({ key: 'features', icon: ICONS.tune, step: stepIndexOf('features'),
                text: on.length > 0 ? `Features on: ${on.join(', ')}` : 'All optional features off' });
        }
        const seedParts: string[] = [];
        if (groupPickCount.value > 0) seedParts.push(plural(groupPickCount.value, 'stock group'));
        if (locationPickCount.value > 0) seedParts.push(plural(locationPickCount.value, 'location'));
        if (seedParts.length > 0) {
            rows.push({ key: 'seed', icon: ICONS.category, step: stepIndexOf('seed'),
                text: seedParts.join(' and ') });
        }
        const itemCount = selectedPackItemsList.value.length + draftItems.value.length;
        if (itemCount > 0) {
            rows.push({ key: 'items', icon: ICONS.inventory_2, step: stepIndexOf('first_item'),
                text: plural(itemCount, 'stock item') });
        }
        if (form.seedDemo) {
            rows.push({ key: 'demo', icon: ICONS.restaurant_menu, step: stepIndexOf('seed'),
                text: 'A demo recipe on this week’s meal plan' });
        }
        return rows;
    });

    // per-name picks over the bundled catalogues. Keys are
    // lowercased (name for groups; "zone" or "zone/child" path for
    // locations). Default state (populated on catalog load) has every
    // name ticked — matches the pre-FU-195 "seedGroups=true" behaviour.
    const groupPicks = reactive<Record<string, boolean>>({});
    const locationPicks = reactive<Record<string, boolean>>({});

    // L30 inline paste-rows affordance state.
    const pasteRowsText = ref('');

    // honoured when the catalogue lands + the
    // pick maps get seeded, so a pre-FU-195 "seedGroups=false" resumes as
    // "no groups picked".
    let legacyGroupsOff = false;
    let legacyLocationsOff = false;

    const firstItem = reactive({
        name: '',
        group_name: null as string | null,
        location_name: null as string | null,
    });

    // Queued first items, awaiting creation on Finish.
    const draftItems = ref<DraftItem[]>([]);

    // starter catalogue (default groups/locations + packs), fetched on
    // mount, and the pack items the user has ticked (keyed by item name).
    const catalog = ref<OnboardingCatalog | null>(null);
    const packItemSelected = reactive<Record<string, boolean>>({});
    async function loadCatalog() {
        try {
            catalog.value = await onboardingApi.getCatalogAsync();
            seedDefaultPicks();
        } catch {
            catalog.value = null;
        }
    }

    // after the catalogue lands, seed the pick maps with every
    // name ticked by default (preserving the pre-FU-195 default of
    // "seed everything"). A pick key already present in the map (from a
    // resumed draft) is left alone so the user's choice survives reload.
    function seedDefaultPicks() {
        if (!catalog.value) return;
        const groupsDefault = legacyGroupsOff ? false : true;
        const locationsDefault = legacyLocationsOff ? false : true;
        for (const name of catalog.value.groups) {
            const key = name.toLowerCase();
            if (!(key in groupPicks)) groupPicks[key] = groupsDefault;
        }
        for (const zone of catalog.value.locations) {
            const zoneKey = zone.name.toLowerCase();
            if (!(zoneKey in locationPicks)) locationPicks[zoneKey] = locationsDefault;
            for (const child of zone.children) {
                const childKey = `${zone.name}/${child.name}`.toLowerCase();
                if (!(childKey in locationPicks)) locationPicks[childKey] = locationsDefault;
            }
        }
    }

    function saveDraft() {
        try {
            const userId = currentUser.value?.user_id ?? '';
            localStorage.setItem(
                DRAFT_KEY(userId),
                JSON.stringify({
                    ...form,
                    stepIndex: stepIndex.value,
                    draftItems: draftItems.value,
                    view: view.value,
                    storySceneIndex: storySceneIndex.value,
                    packItemSelected: { ...packItemSelected },
                    groupPicks: { ...groupPicks },
                    locationPicks: { ...locationPicks },
                    featurePicks: { ...featurePicks },
                }),
            );
        } catch {
            // localStorage may be unavailable.
        }
    }
    function loadDraft() {
        try {
            const userId = currentUser.value?.user_id ?? '';
            const raw = localStorage.getItem(DRAFT_KEY(userId));
            if (!raw) return;
            const parsed = JSON.parse(raw) as Partial<WizardDraft> & {
                stepIndex?: number;
                draftItems?: DraftItem[];
                view?: 'story' | 'setup';
                storySceneIndex?: number;
                packItemSelected?: Record<string, boolean>;
                groupPicks?: Record<string, boolean>;
                locationPicks?: Record<string, boolean>;
                featurePicks?: Partial<Record<FeatureKey, boolean>>;
                // Legacy pre-FU-195 draft booleans — folded into the pick
                // maps once the catalogue lands (seedDefaultPicks respects
                // whatever the pick maps already say).
                seedGroups?: boolean;
                seedLocations?: boolean;
            };
            const {
                stepIndex: savedIndex,
                draftItems: savedItems,
                view: savedView,
                storySceneIndex: savedScene,
                packItemSelected: savedPacks,
                groupPicks: savedGroupPicks,
                locationPicks: savedLocationPicks,
                featurePicks: savedFeatures,
                seedGroups: legacySeedGroups,
                seedLocations: legacySeedLocations,
                ...formFields
            } = parsed;
            Object.assign(form, formFields);
            if (typeof savedIndex === 'number') {
                stepIndex.value = Math.max(0, savedIndex);
            }
            if (Array.isArray(savedItems)) {
                draftItems.value = savedItems;
            }
            if (savedView === 'story' || savedView === 'setup') {
                view.value = savedView;
            }
            if (typeof savedScene === 'number') {
                storySceneIndex.value = Math.max(0, savedScene);
            }
            if (savedPacks) {
                Object.assign(packItemSelected, savedPacks);
            }
            if (savedGroupPicks) {
                Object.assign(groupPicks, savedGroupPicks);
            }
            if (savedLocationPicks) {
                Object.assign(locationPicks, savedLocationPicks);
            }
            if (savedFeatures) {
                savedFeaturePicks = savedFeatures;
                Object.assign(featurePicks, savedFeatures);
            }
            // Legacy pre-FU-195: the booleans became pick maps. If the
            // legacy master was explicitly off, honour that by defaulting
            // any not-yet-populated pick to false (seedDefaultPicks fills
            // absent keys with true; overriding it after mount would race
            // the catalogue fetch).
            legacyGroupsOff = legacySeedGroups === false;
            legacyLocationsOff = legacySeedLocations === false;
        } catch {
            // Bad draft — ignore.
        }
    }
    function clearDraft() {
        try {
            const userId = currentUser.value?.user_id ?? '';
            localStorage.removeItem(DRAFT_KEY(userId));
        } catch {
            // Best effort.
        }
    }
    // Auto-save the draft on any form change so a refresh resumes.
    watch(
        [
            form, stepIndex, draftItems, view, storySceneIndex,
            packItemSelected, groupPicks, locationPicks, featurePicks,
        ],
        saveDraft,
        { deep: true },
    );

    // ── Starter-pack helpers + first-item name options ───────────────
    function uniqueSorted(values: (string | null | undefined)[]): string[] {
        const set = new Set<string>();
        for (const v of values) {
            const name = (v ?? '').trim();
            if (name) set.add(name);
        }
        return [...set].sort((a, b) => a.localeCompare(b));
    }
    // The pack items the user has ticked (catalog packs ∩ packItemSelected),
    // deduped by name (the server dedupes again on create).
    const selectedPackItemsList = computed<StarterPackItem[]>(() => {
        const out: StarterPackItem[] = [];
        const seen = new Set<string>();
        for (const pack of catalog.value?.packs ?? []) {
            for (const item of pack.items) {
                if (packItemSelected[item.name] && !seen.has(item.name)) {
                    seen.add(item.name);
                    out.push(item);
                }
            }
        }
        return out;
    });

    // First-item group/location pickers offer NAMES (resolved server-side on
    // Finish — FU-191): the actually-picked seed defaults (FU-195) + any
    // pack groups + whatever already exists.
    const pickedGroupNames = computed<string[]>(() =>
        (catalog.value?.groups ?? []).filter((n) => groupPicks[n.toLowerCase()]),
    );
    const pickedLocationNames = computed<string[]>(() => {
        const out: string[] = [];
        for (const zone of catalog.value?.locations ?? []) {
            if (locationPicks[zone.name.toLowerCase()]) out.push(zone.name);
            for (const child of zone.children) {
                if (locationPicks[`${zone.name}/${child.name}`.toLowerCase()]) {
                    out.push(child.name);
                }
            }
        }
        return out;
    });
    // Paths in the "Zone" / "Zone/Child" form the server expects — passed
    // straight through to /onboarding/seed's location_paths filter.
    const pickedLocationPaths = computed<string[]>(() => {
        const out: string[] = [];
        for (const zone of catalog.value?.locations ?? []) {
            if (locationPicks[zone.name.toLowerCase()]) out.push(zone.name);
            for (const child of zone.children) {
                const path = `${zone.name}/${child.name}`;
                if (locationPicks[path.toLowerCase()]) out.push(path);
            }
        }
        return out;
    });
    const groupNameOptions = computed(() =>
        uniqueSorted([
            ...pickedGroupNames.value,
            ...selectedPackItemsList.value.map((it) => it.group),
            ...stockGroups.value.map((g) => g.name),
        ]),
    );
    const locationNameOptions = computed(() =>
        uniqueSorted([
            ...pickedLocationNames.value,
            ...selectedPackItemsList.value.map((it) => it.location),
            ...stockLocationStore.stockLocations.map((l) => l.name),
        ]),
    );

    function packSelectedCount(pack: StarterPack): number {
        return pack.items.filter((it) => packItemSelected[it.name]).length;
    }
    function packState(pack: StarterPack): boolean | null {
        const n = packSelectedCount(pack);
        if (n === 0) return false;
        if (n === pack.items.length) return true;
        return null; // some selected → indeterminate
    }
    function togglePack(pack: StarterPack, value: boolean | null) {
        const on = value === true;
        for (const item of pack.items) packItemSelected[item.name] = on;
    }

    // per-name pick helpers for the default groups / locations
    // cards. Master checkbox is tri-state: false = none picked, null =
    // some (indeterminate), true = all. Clicking cycles all-off ⇄ all-on.
    const groupPickCount = computed(() => {
        const names = catalog.value?.groups ?? [];
        return names.filter((n) => groupPicks[n.toLowerCase()]).length;
    });
    const groupMasterState = computed<boolean | null>(() => {
        const total = catalog.value?.groups.length ?? 0;
        const picked = groupPickCount.value;
        if (total === 0 || picked === 0) return false;
        if (picked === total) return true;
        return null;
    });
    function toggleAllGroups(value: boolean | null) {
        const on = value === true;
        for (const n of catalog.value?.groups ?? []) {
            groupPicks[n.toLowerCase()] = on;
        }
    }
    // Location paths ("zone" or "zone/child") the user has ticked, in
    // the same order the catalogue lists them.
    const locationLeafPaths = computed<string[]>(() => {
        const out: string[] = [];
        for (const zone of catalog.value?.locations ?? []) {
            out.push(zone.name);
            for (const child of zone.children) {
                out.push(`${zone.name}/${child.name}`);
            }
        }
        return out;
    });
    const locationPickCount = computed(
        () => locationLeafPaths.value.filter((p) => locationPicks[p.toLowerCase()]).length,
    );
    const locationMasterState = computed<boolean | null>(() => {
        const total = locationLeafPaths.value.length;
        const picked = locationPickCount.value;
        if (total === 0 || picked === 0) return false;
        if (picked === total) return true;
        return null;
    });
    function toggleAllLocations(value: boolean | null) {
        const on = value === true;
        for (const p of locationLeafPaths.value) locationPicks[p.toLowerCase()] = on;
    }

    // parse the paste-rows textarea. One row per line;
    // fields comma-separated: Name, Group?, Location?. Empty lines and
    // rows without a Name are dropped silently.
    const pasteRowsParsed = computed<DraftItem[]>(() => {
        const rows: DraftItem[] = [];
        for (const rawLine of pasteRowsText.value.split(/\r?\n/)) {
            const line = rawLine.trim();
            if (!line) continue;
            const parts = line.split(',').map((p) => p.trim());
            const name = parts[0] ?? '';
            if (!name) continue;
            rows.push({
                name,
                group_name: parts[1] ? parts[1] : null,
                location_name: parts[2] ? parts[2] : null,
            });
        }
        return rows;
    });
    function queuePastedRows() {
        const rows = pasteRowsParsed.value;
        if (rows.length === 0) return;
        draftItems.value.push(...rows);
        const n = rows.length;
        pasteRowsText.value = '';
        $q.notify({
            type: 'positive',
            position: 'bottom-right',
            message: `Queued ${n} row${n === 1 ? '' : 's'}, saved when you finish.`,
        });
    }

    // ── Navigation ───────────────────────────────────────────────────
    function onBack() {
        // On the first setup step, "Back" returns the user to the story
        // section instead of being a dead-end disabled button.
        if (stepIndex.value === 0) {
            view.value = 'story';
            return;
        }
        stepIndex.value--;
    }

    // Next / Finish. Advancing a step has NO side effects now — every
    // choice (prefs, seeds, queued items) is applied once, in complete(),
    // so a mid-wizard bail leaves the account untouched (L35). The final
    // step triggers that one-shot apply.
    function advance() {
        if (isLastStep.value) {
            void finish('/');
            return;
        }
        stepIndex.value++;
    }

    // Finish (or "Show me X") = apply the draft, then navigate. On a failed
    // apply we stay put with the error shown so the user can fix + retry.
    async function finish(destination: string) {
        if (await complete()) void router.push(destination);
    }

    // Apply everything the user chose, once, in dependency order: prefs →
    // persona → seed catalogues → stock items (pack picks + queued first
    // items), so the items resolve against the groups/locations just seeded.
    async function applyDraft() {
        await persistPreferences();
        // Features before seeding so anything the seed or items pass reads
        // (e.g. stocktake defaults) sees the household's choice.
        const featureUpdates = changedFeatureSettings.value;
        if (Object.keys(featureUpdates).length > 0) {
            await appSettingsApi.updateAsync(featureUpdates);
            featureBaseline.value = { ...featurePicks };
            await refreshFeatureFlags();
        }
        // send the actual picked names/paths. Master bool is
        // implicit: it's true whenever any pick under it survives.
        const groupsWanted = groupPickCount.value > 0;
        const locationsWanted = locationPickCount.value > 0;
        if (groupsWanted || locationsWanted) {
            const totalGroups = catalog.value?.groups.length ?? 0;
            const totalLocations = locationLeafPaths.value.length;
            const allGroupsPicked = groupPickCount.value === totalGroups;
            const allLocationsPicked = locationPickCount.value === totalLocations;
            await onboardingApi.seedAsync({
                groups: groupsWanted,
                locations: locationsWanted,
                // Null when the user wants everything → matches the "seed
                // all defaults" semantic on the server (and keeps the wire
                // payload tiny in the common case).
                group_names: groupsWanted && !allGroupsPicked
                    ? pickedGroupNames.value : null,
                location_paths: locationsWanted && !allLocationsPicked
                    ? pickedLocationPaths.value : null,
            });
        }
        // Pack picks + first items, created by NAME (server resolves group /
        // location against the just-seeded catalogues — FU-191 — and dedupes).
        const items = [
            ...selectedPackItemsList.value.map((it) => ({
                name: it.name,
                group_name: it.group,
                location_name: it.location,
            })),
            ...draftItems.value.map((d) => ({
                name: d.name,
                group_name: d.group_name,
                location_name: d.location_name,
            })),
        ];
        if (items.length > 0) {
            await onboardingApi.seedItemsAsync({ items });
        }
        // optional demo dataset. After the items pass so the demo
        // can reuse a starter-pack "Spaghetti pasta" / "Garlic" / "Olive oil"
        // if the user picked them; otherwise the demo creates its own. The
        // server is idempotent (`seeded: false` when the demo recipe already
        // exists) so a re-finish never duplicates.
        if (form.seedDemo) {
            await onboardingApi.seedDemoAsync();
        }
    }

    function handleApplyError(err: unknown) {
        const extracted = extractFieldErrors(err);
        const remainingFields = Object.values(extracted.fieldErrors).filter(Boolean);
        loadError.value =
            [extracted.generalError, ...remainingFields].filter(Boolean).join(' ') ||
            "Couldn't finish setting up. Please try again.";
    }

    async function persistPreferences() {
        // Display name is no longer collected here — it's fixed at account
        // creation (the username picked at register time). Onboarding only
        // touches personal look (theme + font); household cooking config
        // (headcount + cook-style) is install-wide now (FU-615).
        const updates: Record<string, unknown> = {};
        if (form.theme !== currentUser.value?.theme) {
            updates.theme = form.theme;
        }
        if (form.fontFamily !== currentUser.value?.font_family) {
            updates.font_family = form.fontFamily;
        }
        if (form.avatarDataUrl) {
            updates.image = form.avatarDataUrl;
        }
        if (Object.keys(updates).length === 0) return;
        await authStore.updateMeAsync(updates);
    }

    function onAddFirstItem() {
        const name = firstItem.name.trim();
        if (!name) return;
        // Queue, don't persist — created on Finish so a bail leaves nothing (L35).
        draftItems.value.push({
            name,
            group_name: firstItem.group_name,
            location_name: firstItem.location_name,
        });
        firstItem.name = '';
        $q.notify({
            type: 'positive',
            position: 'bottom-right',
            message: 'Added. Saved when you finish.',
        });
    }

    function removeDraftItem(index: number) {
        draftItems.value.splice(index, 1);
    }

    function onShowMe(path: string) {
        // "Show me X" = finish onboarding (applying the draft), then land on
        // that screen.
        void finish(path);
    }

    async function onSkipEverything() {
        completing.value = true;
        try {
            // Persist the timestamp + drop a flag so the dashboard can
            // show a 24h "finish setting up" banner.
            await onboardingApi.completeAsync();
            // Refresh the cached user so the router guard sees the new
            // `onboarding_completed_at`. Without this, the guard reads the
            // stale (null) value and bounces the user straight back to
            // /welcome — making the button look dead until a hard refresh.
            await authStore.refreshAsync();
            try {
                localStorage.setItem(
                    'dora.onboarding.skipped_at',
                    new Date().toISOString(),
                );
            } catch {
                // Ignore — banner just won't fire.
            }
            clearDraft();
            void router.push('/');
        } catch (err) {
            const extracted = extractFieldErrors(err);
            loadError.value =
                extracted.generalError ?? "Couldn't skip onboarding. Please try again.";
        } finally {
            completing.value = false;
        }
    }

    // Apply the collected draft + stamp completion. Returns true on success;
    // the caller navigates (Finish → '/', Show-me → the chosen path) so a
    // failed apply keeps the user in the wizard with the error shown.
    async function complete(): Promise<boolean> {
        completing.value = true;
        loadError.value = null;
        try {
            await applyDraft();
            await onboardingApi.completeAsync();
            // Refresh the cached user so the router guard sees the new
            // `onboarding_completed_at`. Without this, Finish / Show-me-X
            // navigations bounce straight back to /welcome on the first
            // attempt (the guard reads stale null); user only escapes
            // after a hard refresh re-bootstraps the auth state.
            await authStore.refreshAsync();
            // The picture is saved now; drop the draft copy so a re-run of
            // the wizard doesn't re-upload it.
            form.avatarDataUrl = null;
            form.avatarPresetKey = null;
            clearDraft();
            // Clear any stale "skipped" flag so the dashboard banner
            // doesn't reappear after a proper completion.
            try {
                localStorage.removeItem('dora.onboarding.skipped_at');
            } catch {
                // Ignore.
            }
            return true;
        } catch (err) {
            handleApplyError(err);
            return false;
        } finally {
            completing.value = false;
        }
    }

    onMounted(async () => {
        try {
            state.value = await onboardingApi.getStateAsync();
        } catch (err) {
            const extracted = extractFieldErrors(err);
            loadError.value =
                extracted.generalError ?? "Couldn't load onboarding state. Please refresh.";
        }
        // Seed theme/font from the user's saved values, then layer the saved
        // draft on top. Display name is set at account creation; household
        // cooking config is install-wide (FU-615) — neither is collected here.
        if (currentUser.value) {
            // Pre-fill from the user's saved prefs. If their stored theme
            // isn't one of the three onboarding options (e.g. they picked a
            // richer palette in Preferences on a re-run), the select shows
            // blank and persistPreferences leaves it untouched — we never
            // clobber a real choice.
            form.theme = currentUser.value.theme ?? 'system';
            form.fontFamily = coalesceFontFamily(currentUser.value.font_family);
        }
        loadDraft();
        void loadFeatureBaseline();

        // Pre-load existing groups/locations (so the first-item name pickers
        // include what's already there) + the starter catalogue (default
        // names + packs to preview and pick from).
        await Promise.all([
            loadStockGroups(),
            stockLocationStore.stockLocations.length === 0
                ? stockLocationStore.getStockLocationsAsync()
                : Promise.resolve(),
            loadCatalog(),
        ]);
    });
</script>

<style scoped>
    .wizard-shell {
        max-width: 720px;
    }
    /* Slim top row — mascot · progress rail · skip escape — with generous
       horizontal spacing between the three so it reads as one clean band. */
    .wizard-topbar {
        display: flex;
        align-items: center;
        gap: var(--space-5);
    }
    .wizard-topbar-rail {
        flex: 1 1 auto;
        min-width: 0;
    }
    .wizard-mascot,
    .wizard-skip {
        flex: 0 0 auto;
    }
    /* Bounds the absolutely-positioned finish confetti to the step. */
    .finish-step {
        position: relative;
    }
    .seed-card {
        cursor: pointer;
        transition: outline-color 120ms ease, transform 120ms ease,
            box-shadow 120ms ease;
        outline: 2px solid transparent;
        outline-offset: -2px;
        height: 100%;
    }
    .seed-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 14px var(--overlay-active);
    }
    .seed-card--picked {
        outline-color: var(--q-primary);
    }
    .full-height {
        height: 100%;
    }
    /* ── Welcome step (2026-10-17 rebuild) ─────────────────────────── */
    .welcome-step {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
    }
    .welcome-hero {
        display: flex;
        align-items: center;
        gap: var(--space-5);
        padding: var(--space-5);
        border-radius: var(--radius-lg);
        background: var(--hero-gradient);
        border: 1px solid var(--border-default);
    }
    .welcome-hero__avatar {
        position: relative;
        flex: 0 0 auto;
    }
    .welcome-hero__avatar :deep(.image-edit-tile) {
        box-shadow: 0 0 0 4px var(--surface-component), 0 8px 24px var(--overlay-active);
        border-radius: 50%;
    }
    .welcome-hero__mascot {
        position: absolute;
        right: -14px;
        bottom: -10px;
        width: 44px;
        height: 44px;
        pointer-events: none;
        filter: drop-shadow(0 2px 4px var(--overlay-active));
    }
    .welcome-hero__copy {
        min-width: 0;
    }
    .welcome-hero__kicker {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--brand-secondary);
    }
    .welcome-hero__title {
        margin: 2px 0 6px;
        font-size: 1.6rem;
        line-height: 1.2;
        font-weight: 700;
        color: var(--text-primary);
        overflow-wrap: anywhere;
    }
    .welcome-hero__blurb {
        margin: 0;
        font-size: 0.95rem;
        line-height: 1.5;
        color: var(--text-secondary);
    }
    .welcome-panel {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
        padding: var(--space-4) var(--space-5);
        border-radius: var(--radius-lg);
        background: var(--surface-component);
        border: 1px solid var(--border-default);
    }
    .welcome-panel__title {
        font-size: 1rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .welcome-panel__sub {
        font-size: 0.85rem;
        color: var(--text-muted);
    }
    .welcome-panel__foot {
        display: flex;
        align-items: center;
        min-height: 32px;
    }
    .welcome-themes {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: var(--space-3);
    }
    .welcome-theme {
        position: relative;
        appearance: none;
        display: flex;
        flex-direction: column;
        gap: var(--space-2);
        padding: var(--space-2);
        border: 1.5px solid var(--border-default);
        border-radius: var(--radius-md);
        background: var(--surface-component);
        color: var(--text-primary);
        cursor: pointer;
        text-align: left;
        transition: border-color var(--motion-fast) var(--motion-ease),
            transform var(--motion-fast) var(--motion-ease);
    }
    .welcome-theme:hover {
        border-color: var(--border-strong);
        transform: translateY(-1px);
    }
    .welcome-theme:focus-visible {
        outline: 2px solid var(--accent-mark);
        outline-offset: 2px;
    }
    .welcome-theme--active {
        border-color: var(--accent-mark);
        border-width: 2px;
    }
    .welcome-theme__preview {
        display: flex;
        height: 64px;
        border-radius: var(--radius-sm);
        overflow: hidden;
        border: 1px solid var(--border-default);
    }
    /* Each half is painted in its own theme's tokens via `data-theme`. */
    .welcome-theme__half {
        flex: 1 1 0;
        display: flex;
        flex-direction: column;
        gap: 5px;
        padding: 0 0 6px;
        background: var(--surface-page);
        position: relative;
    }
    .welcome-theme__bar {
        height: 12px;
        background: var(--brand-primary);
    }
    .welcome-theme__line {
        height: 6px;
        margin: 0 8px;
        border-radius: 3px;
        background: var(--surface-component);
    }
    .welcome-theme__line--short {
        width: 45%;
    }
    .welcome-theme__dot {
        position: absolute;
        right: 8px;
        bottom: 6px;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background: var(--brand-accent);
    }
    .welcome-theme__label {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .welcome-theme__badge {
        position: absolute;
        top: 4px;
        right: 4px;
        color: var(--accent-mark);
        background: var(--surface-component);
        border-radius: 50%;
    }
    .welcome-font {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .welcome-font__label {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-secondary);
    }

    /* ── Features step ─────────────────────────────────────────────── */
    .features-step__head {
        margin-bottom: var(--space-4);
    }
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr));
        gap: var(--space-3);
    }
    .feature-card {
        appearance: none;
        display: flex;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-4);
        border: 1.5px solid var(--border-default);
        border-radius: var(--radius-lg);
        background: var(--surface-component);
        color: var(--text-primary);
        text-align: left;
        cursor: pointer;
        transition: border-color var(--motion-fast) var(--motion-ease),
            background var(--motion-fast) var(--motion-ease),
            transform var(--motion-fast) var(--motion-ease);
    }
    .feature-card:hover:not(:disabled) {
        border-color: var(--border-strong);
        transform: translateY(-1px);
    }
    .feature-card:focus-visible {
        outline: 2px solid var(--accent-mark);
        outline-offset: 2px;
    }
    .feature-card:disabled {
        cursor: default;
        opacity: 0.6;
    }
    .feature-card--on {
        border-color: var(--brand-primary);
        background: color-mix(in srgb, var(--brand-primary-soft) 45%, var(--surface-component));
    }
    .feature-card__icon {
        flex: 0 0 auto;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: color-mix(in srgb, var(--text-muted) 16%, var(--surface-component));
        color: var(--text-secondary);
        transition: background var(--motion-fast) var(--motion-ease),
            color var(--motion-fast) var(--motion-ease);
    }
    .feature-card--on .feature-card__icon {
        background: var(--brand-primary-soft);
        color: var(--brand-primary);
    }
    .feature-card__body {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .feature-card__title {
        font-size: 0.95rem;
        font-weight: 700;
    }
    .feature-card__desc {
        font-size: 0.82rem;
        line-height: 1.4;
        color: var(--text-secondary);
    }
    .feature-card__state {
        flex: 0 0 auto;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        color: var(--text-muted);
    }
    .feature-card--on .feature-card__state {
        color: var(--brand-primary);
    }
    .feature-card__state-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* ── Finish step ───────────────────────────────────────────────── */
    .finish-step {
        display: flex;
        flex-direction: column;
        gap: var(--space-4);
    }
    .finish-hero {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: var(--space-2);
        padding: var(--space-5) var(--space-4);
        border-radius: var(--radius-lg);
        background: var(--hero-gradient);
        border: 1px solid var(--border-default);
    }
    .finish-hero__faces {
        display: flex;
        align-items: flex-end;
        justify-content: center;
    }
    .finish-hero__avatar {
        box-shadow: 0 0 0 4px var(--surface-component), 0 8px 24px var(--overlay-active);
        z-index: 1;
    }
    .finish-hero__mascot {
        margin-left: -18px;
    }
    .finish-hero__title {
        font-size: 1.6rem;
        font-weight: 700;
        line-height: 1.2;
        color: var(--text-primary);
        overflow-wrap: anywhere;
    }
    .finish-hero__sub {
        max-width: 30rem;
        font-size: 0.95rem;
        color: var(--text-secondary);
    }
    .finish-panel {
        display: flex;
        flex-direction: column;
        gap: var(--space-3);
    }
    .finish-panel__title {
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-muted);
    }
    .finish-recap {
        list-style: none;
        margin: 0;
        padding: var(--space-1) var(--space-4);
        border-radius: var(--radius-lg);
        background: var(--surface-component);
        border: 1px solid var(--border-default);
    }
    .finish-recap__row {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        min-height: 44px;
        padding: 4px 0;
    }
    .finish-recap__row + .finish-recap__row {
        border-top: 1px solid var(--divider);
    }
    .finish-recap__icon {
        flex: 0 0 auto;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--brand-primary-soft);
        color: var(--brand-primary);
    }
    .finish-recap__text {
        flex: 1 1 auto;
        min-width: 0;
        font-size: 0.9rem;
        color: var(--text-primary);
    }
    .finish-tiles {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr));
        gap: var(--space-3);
    }
    .finish-tile {
        appearance: none;
        display: flex;
        align-items: center;
        gap: var(--space-3);
        padding: var(--space-3) var(--space-4);
        border: 1px solid var(--border-default);
        border-radius: var(--radius-lg);
        background: var(--surface-component);
        color: var(--text-primary);
        text-align: left;
        cursor: pointer;
        transition: border-color var(--motion-fast) var(--motion-ease),
            transform var(--motion-fast) var(--motion-ease),
            box-shadow var(--motion-fast) var(--motion-ease);
    }
    .finish-tile:hover:not(:disabled) {
        border-color: var(--brand-primary);
        transform: translateY(-2px);
        box-shadow: 0 6px 16px var(--overlay-active);
    }
    .finish-tile:focus-visible {
        outline: 2px solid var(--accent-mark);
        outline-offset: 2px;
    }
    .finish-tile:disabled {
        cursor: default;
        opacity: 0.6;
    }
    .finish-tile__icon {
        flex: 0 0 auto;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--brand-primary-soft);
        color: var(--brand-primary);
    }
    .finish-tile__body {
        flex: 1 1 auto;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .finish-tile__title {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.95rem;
        font-weight: 700;
    }
    .finish-tile__num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 18px;
        height: 18px;
        border-radius: 50%;
        font-size: 0.7rem;
        background: var(--brand-primary);
        color: var(--text-on-primary);
    }
    .finish-tile__desc {
        font-size: 0.82rem;
        line-height: 1.4;
        color: var(--text-secondary);
    }
    .finish-tile__chevron {
        flex: 0 0 auto;
        color: var(--text-muted);
    }
    .finish-tip {
        display: flex;
        align-items: flex-start;
        gap: var(--space-2);
        padding: var(--space-3) var(--space-4);
        border-radius: var(--radius-md);
        background: var(--surface-sunken);
        font-size: 0.875rem;
        color: var(--text-secondary);
    }
    .finish-tip__icon {
        flex: 0 0 auto;
        color: var(--brand-secondary);
    }

    @media (max-width: 599px) {
        .welcome-hero {
            flex-direction: column;
            text-align: center;
            padding: var(--space-4);
        }
        .welcome-panel {
            padding: var(--space-3) var(--space-4);
        }
        .welcome-themes {
            gap: var(--space-2);
        }
    }
</style>
