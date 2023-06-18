/*
 * Copyright (c) 2019 SuccessFactors, Inc
 */

package com.successfactors.android.tests.uxr.managerpanel

import androidx.test.filters.LargeTest
import com.successfactors.android.Rules.RuleEnum
import com.successfactors.android.annotations.SFTestAttribute
import com.successfactors.android.annotations.TestLinkId
import com.successfactors.android.pages.profile.ProfilePage
import com.successfactors.android.pages.uxr.cpm.UxrCPMActivityListPage
import com.successfactors.android.pages.uxr.managerpanel.UxrCPMManagerPanelPage
import com.successfactors.android.tests.uxr.cpm.UxrCPMCommonTest
import com.successfactors.android.utils.SFTestLogger
import com.successfactors.android.utils.TestData
import com.successfactors.android.utils.LoggingJUnitParamsRunner
import junitparams.Parameters
import org.junit.*
import org.junit.rules.TestName
import org.junit.runner.RunWith
import org.junit.runners.MethodSorters

/**
 * Created by i520130(jack.pan01@sap.com) on 2019/09/23
 */

@RunWith(LoggingJUnitParamsRunner::class)
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
@LargeTest
class UxrCPMManagerPanelDemoTest : UxrCPMCommonTest() {

    @get:Rule
    var testName: TestName = TestName()

    var retryTime = 2

    val TAG = this.javaClass.simpleName

    private var result = false

    override fun getFileName(): String {
        return "json/uxr/managerpanel/UxrCPMManagerPanelDemoTest.json"
    }

    @Before
    fun beforeMethodBeforeEachTest() {
        SFTestLogger.info(TAG, "====== Test Start [${testName.methodName.split("(")[0]}]")
        result = false
    }

    @After
    fun afterMethodBeforeEachTest() {
        SFTestLogger.info(TAG, "====== Test Result ${if (result) "Pass" else "Fail"} [${testName.methodName.split("(")[0]}]")
    }

    private fun managerPanel_allInfo(): Any {
        return getTestData("managerPanel_allInfo")
    }

    @Test
    @Parameters(method = "managerPanel_allInfo")
    @TestLinkId(id = ["MOB-37645"], description = ["Verify that enter manager team panel page when permitted",
        "Verify elements including name, title, VIEW PROFILE, call, msg, email, add_to_contact in profileHeader"])
    @SFTestAttribute(
        "Claire Huang",
        "MOB-37643",
        "uxrcpm",
        RuleEnum.Priority.P3,
        RuleEnum.Category.Regression,
        data.get("username"),
        "Instance",
        "1. check CPM items shown/ not shown by RBP" +
            "2. click Activities item",
        ""
    )
   fun test1(data: TestData) {
        reRun({
            startAppFromLauncher(data).run {
                safeDismissInfoTextOnHome()
                openNavDrawer()
            }.navigateToTeamPage().run {
                waitForRefreshIndicatorDisappear()
            }.navigateToUxrCPMManagerPanelPage(data.get("DRName")).run {
                waitForRefreshIndicatorDisappear<UxrCPMManagerPanelPage>()

                isTitlePresent(data.get("DRName"))
                isSubTitlePresent(data.get("jobTitle"))
                isViewProfilePresent()
            }.clickViewProfileIfPresent().run {
                waitForRefreshIndicatorDisappear<ProfilePage>()
                navigateBack()
                openNavDrawer()
            }.navigateBackToHomePage()

            result = true
        }, retryTime)
    }

    @Test
    @Parameters(method = "managerPanel_allInfo")
    @TestLinkId(id = ["MOB-37645"], description = ["Verify that enter manager team panel page when permitted",
        "Verify elements including name, title, VIEW PROFILE, call, msg, email, add_to_contact in profileHeader"])
    @SFTestAttribute(
        "Claire Huang",
        "MOB-37645",
        "uxrcpm",
        RuleEnum.Priority.P2,
        RuleEnum.Category.Regression,
        data.get("username"),
        "Instance",
        "1. open manager team panel page, check the profile header view" +
            "2. click VIEW PROFILE",
        ""
    )
   fun test2(data: TestData) {
        reRun({
            startAppFromLauncher(data).run {
                safeDismissInfoTextOnHome()
                openNavDrawer()
            }.navigateToTeamPage().run {
                waitForRefreshIndicatorDisappear()
            }.navigateToUxrCPMManagerPanelPage(data.get("DRName")).run {
                waitForRefreshIndicatorDisappear<UxrCPMManagerPanelPage>()

                isTitlePresent(data.get("DRName"))
                isSubTitlePresent(data.get("jobTitle"))
                isViewProfilePresent()
            }.clickViewProfileIfPresent().run {
                waitForRefreshIndicatorDisappear<ProfilePage>()
                navigateBack()
                openNavDrawer()
            }.navigateBackToHomePage()

            result = true
        }, retryTime)
    }
}